"""PyLabware connection adapters."""

import logging
import socket
import sys
import threading
from abc import ABC, abstractmethod
from time import sleep, time
from urllib.parse import urljoin
from typing import Any, Dict

import requests
import serial

from .exceptions import PLConnectionError, PLConnectionProtocolError, PLConnectionTimeoutError
from .models import LabDeviceReply, ConnectionParameters


class AbstractConnection(ABC):
    """Base abstract class for all connection adapters.
    """

    DEFAULT_CONNECTION_PARAMETERS = {
        # Default connection address
        "address": None,

        # Connection port
        "port": "",

        # Default encoding for text data
        "encoding": "UTF-8",

        # command_delay serves as a flow control to ensure that device has time
        # to process the command before issuing another one.This is not an issue
        # for high-level transports, such as HTTP, because network stack latency
        # adds some delay, but it is a problem for low-level protocols like
        # RS-232 or RS-485 if hardware flow-control is not implemented.
        "command_delay": 0.5,

        # Buffer size for reading incoming data, bytes
        # Typically, serial communiation with devices is reply based rather
        # than stream based. However, not all devices behave themselves,
        # replying with properly terminated strings, so it becomes unreliable to
        # detect end of message here on transport level. Thus connection operates
        # as a stream device, quickly reading data back in fixed-size chunks and
        # passing them to upper level (controller) for assembly
        "receive_buffer_size": 128,

        # Receive timeout in seconds.
        "receive_timeout": 1,

        # Transmit timeout in seconds
        "transmit_timeout": 1,

        # Delay for the connection listener loop to check for new data
        # TODO maybe this can be replaced by a multiple of receive_timeout
        "receiving_interval": 0.05
    }  # type: ConnectionParameters

    @abstractmethod
    def __init__(self, connection_parameters: ConnectionParameters):
        """
        Args:
            connection_parameters: Dictionary with connection settings
                                   relevant for the concrete type of connection.
        """

        # Get logger object
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Merge default dict with provided dict to give connection parameter dict
        self.connection_parameters = {**self.DEFAULT_CONNECTION_PARAMETERS, **connection_parameters}
        self.logger.info("Creating connection object with the following settings: \n%s", self.connection_parameters)

        # Empty connection object
        self._connection: Any = None
        # Lock for thread-safe access to connection object
        self._connection_lock = threading.Lock()
        # Flag for thread-safe access to received data
        self._data_ready = threading.Event()
        self._data_ready.clear()
        # Last reply from the device
        self._last_reply = ""
        # Time when last command was sent to the device
        self._last_command_time = time()

        # Common connection parameters
        self.encoding = self.connection_parameters["encoding"]
        self.receive_buffer_size = self.connection_parameters["receive_buffer_size"]
        self.command_delay = self.connection_parameters["command_delay"]
        self.transmit_timeout = self.connection_parameters["transmit_timeout"]
        self.receive_timeout = self.connection_parameters["receive_timeout"]

    @abstractmethod
    def open_connection(self):
        """Opens the connection. This method should create self._connection object,
        set up necessary parameters and open connection. Connection object
        creation shouldn't be done in __init__(), otherwise the connection object
        instance might not be reusable after close()-open() sequence.

        This method has to be redefined in child classes.
        """

    @abstractmethod
    def close_connection(self):
        """Closes the connection.

        This method has to be redefined in child classes.
        """

    @abstractmethod
    def is_connection_open(self):
        """Checks whether the connection is open.

        This method has to be redefined in child classes.

        Returns:
            (bool): True if connection is open, False if connection is closed.
        """

    @abstractmethod
    def transmit(self, msg: str):
        """Transmits the data to the device.

        This method has to be redefined in child classes.

        Arguments:
            msg (str): Data to send.
        """

    @abstractmethod
    def receive(self):
        """Receives data from the device

        This method has to be redefined in child classes.

        Returns:
            (str): Data from the device.
        """

    def _clear_data_buffer(self):
        """Debug method to remove accidentally stuck data from the buffer
        between connection closing/re-opening.
        """

        self._data_ready.clear()
        self._last_reply = ""


class SerialConnection(AbstractConnection):
    """Serial connection adapter.
    """

    SERIAL_DEFAULT_CONNECTION_PARAMETERS = {
        "write_timeout": 0.5,
        "baudrate": 9600,
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_NONE,
        "stopbits": serial.STOPBITS_ONE,
        "xonxoff": False,
        "rtscts": False,
        "dsrdtr": False,
        "inter_byte_timeout": False,
    }  # type: ConnectionParameters

    def __init__(self, connection_parameters: ConnectionParameters):
        """
        Args:
            connection_parameters: Dictionary with connection settings relevant for the serial connection.
        """

        # Init base class, set common parameters
        config = {**self.SERIAL_DEFAULT_CONNECTION_PARAMETERS, **connection_parameters}
        super().__init__(config)

        # Interval in seconds for connection listener to check for incoming data
        # This is the time that connection listener sleeps between serial port read attempts
        # So this determines the maximum delay between reply received and reply being read out.
        self.receiving_interval = self.connection_parameters.get("receiving_interval")

        # Connection listener thread settings
        self.listener = None
        self._connection_close_requested = threading.Event()
        self._connection_close_requested.clear()

    def open_connection(self):
        """Creates, sets up and opens serial connection.
        """

        # Create serial connection object
        # port=None is required to prevent port from being immediately opened
        # TODO add here & for TCPIP check is connection already open
        self._connection = serial.Serial(port=None)
        self._clear_data_buffer()
        # Load settings
        self._connection.port = self.connection_parameters.get("port")
        self._connection.baudrate = self.connection_parameters.get("baudrate")
        self._connection.bytesize = self.connection_parameters.get("bytesize")
        self._connection.parity = self.connection_parameters.get("parity")
        self._connection.stopbits = self.connection_parameters.get("stopbits")
        self._connection.timeout = self.connection_parameters.get("timeout", self.receive_timeout)
        self._connection.xonxoff = self.connection_parameters.get("xonxoff")
        self._connection.rtscts = self.connection_parameters.get("rtscts")
        self._connection.dsrdtr = self.connection_parameters.get("dsrdtr")
        self._connection.write_timeout = self.transmit_timeout
        self._connection.inter_byte_timeout = self.connection_parameters.get("inter_byte_timeout")
        # Open connection
        try:
            self._connection.open()
        except serial.SerialException as e:
            raise PLConnectionError(f"Can't open serial port {self._connection.port}!") from e
        # Start connection listener
        self.listener = threading.Thread(target=self.connection_listener, name="{}_listener".format(__name__), daemon=True)
        self._connection_close_requested.clear()
        self.listener.start()
        self.logger.info("Port %s opened.", self._connection.port)

    def connection_listener(self):
        """Periodically checks for new data on the connection,
        reads it, puts the data read into receive buffer and raises data ready flag.
        """

        self.logger.info("Starting connection listener...")
        while True:
            # Check connection close request
            if self._connection_close_requested.is_set():
                self.logger.info("Connection listener exiting.")
                return
            if self._connection.in_waiting > 0:
                # If the flag is still set it means receive() hasn't yet read it out
                if self._data_ready.is_set() is True:
                    self.logger.warning("Discarding unconsumed device reply <%r>", self._last_reply)
                self._last_reply = ""
                # Read data from connection into buffer
                while self._connection.in_waiting > 0 and len(self._last_reply) <= self.receive_buffer_size:
                    self.logger.debug("connection_listener()::<%s> bytes to read", self._connection.in_waiting)
                    # Lock connection
                    with self._connection_lock:
                        reply_bytes = self._connection.read(size=self.receive_buffer_size)
                        self.logger.debug("connection_listener()::got reply <%s>", reply_bytes)
                    try:
                        self._last_reply += reply_bytes.decode(self.encoding)
                    except UnicodeDecodeError:
                        self.logger.exception("Can't decode device reply!", exc_info=True)
                        # Unlock connection & break to outer loop discarding current data
                        break
                # Notify main thread that it can access _last_reply now
                self._data_ready.set()
            # Switch thread context to main
            sleep(self.receiving_interval)

    def close_connection(self):
        """Closes serial connection.
        """

        if self.is_connection_open():
            # Stop connection listener
            self._connection_close_requested.set()
            self.listener.join(timeout=self.receiving_interval * 5)
            self._connection.reset_input_buffer()
            self._connection.reset_output_buffer()
            self._connection.close()
            self.logger.info("Port %s closed.", self._connection.port)
        else:
            self.logger.warning("Trying to close port <%s> that is not open", self._connection.port)

    def is_connection_open(self) -> bool:
        """Checks whether the serial port is opened.

        Returns:
            (bool): If the serial port is open.
        """

        # Serial connection open status
        if self._connection is None:
            return False
        is_open = self._connection.is_open
        # Check & warn if connection is open, but connection listener thread is not running
        if is_open and not self.listener.is_alive():  # type: ignore
            self.logger.warning("Connection listener thread seems to be dead!")
        return is_open

    def transmit(self, msg: str):
        """Sends message to the serial port.
        """

        # Check if connection is alive
        if not self.is_connection_open():
            raise PLConnectionError("No connection to the device!")
        try:
            command = msg.encode(self.encoding)
        except SyntaxError:
            raise PLConnectionProtocolError("Can't encode command <{}> to a byte-string!".format(msg)) from None
        # Calculate if we have to wait after the previous command was sent
        delta = time() - self._last_command_time
        # Subtract 0.5 second for possible jitter/precision errors
        if delta < self.command_delay:
            self.logger.debug("Command rate too high! Delaying next command for %s seconds", self.command_delay)
            sleep(self.command_delay - delta)
        if self._data_ready.is_set() is True:
            self.logger.warning("Previous reply <%s> has not been read.", self._last_reply)
        with self._connection_lock:
            self._connection.reset_input_buffer()
            self._connection.reset_output_buffer()
            self._connection.write(command)
        self._last_command_time = time()
        self.logger.debug("transmit()::sent command <%s>", command)

    def receive(self, retries: int = 3):
        """Gets the data from receive buffer, clears the data ready flag
        and passes the data back.

        Returns:
            (LabDeviceReply): Reply from the device packed into LabDeviceReply object.

        """

        if not self._data_ready.is_set():
            self.logger.debug("receive()::waiting for incoming data to become ready...")
            failed_attempts = 0
            # Timeout here ensures upper level code wouldn't lock forever if no reply is received
            # It has to be long enough to give time for connection_listener() thread to do it's job
            while self._data_ready.wait(timeout=self.receive_timeout * 10) is False:
                failed_attempts += 1
                if failed_attempts > retries:
                    # No reply after timeout
                    raise PLConnectionTimeoutError("No reply received from the device!")

        # Unset ready flag
        self._data_ready.clear()
        return LabDeviceReply(body=self._last_reply, content_type="chunked")


class TCPIPConnection(AbstractConnection):
    """Socket-based TCP/IP connection adapter.
    """

    TCPIP_DEFAULT_CONNECTION_PARAMETERS = {
        "protocol": "TCP",
    }  # type: ConnectionParameters

    def __init__(self, connection_parameters: ConnectionParameters):
        """Default constructor.

        Args:
            connection_parameters: Dictionary with connection settings for socket-based connection.
        """

        # Init base class, set common parameters
        config = {**self.TCPIP_DEFAULT_CONNECTION_PARAMETERS, **connection_parameters}
        super().__init__(config)
        # Default IP connection settings
        self.address = self.connection_parameters.get("address")
        self.port = self.connection_parameters.get("port")
        self.protocol = self.connection_parameters["protocol"].upper()

        # Connection listener thread settings
        self.listener = None
        self._connection_close_requested = threading.Event()
        self._connection_close_requested.clear()

        # Interval in seconds for connection listener to check for incoming data
        # This is the time that connection listener sleeps between serial port read attempts
        # So this determines the maximum delay between reply received and reply being read out.
        self.receiving_interval = self.connection_parameters.get("receiving_interval")

    def open_connection(self):
        """Creates, sets up and and opens the socket.
        """

        try:
            # Initialize TCP socket connection object
            if self.protocol == "TCP":
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif self.protocol == "UDP":
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                raise PLConnectionProtocolError("Unknown transport layer protocol <{}> provided!".format(self.protocol))

            self._clear_data_buffer()
            self._connection.connect((self.address, int(self.port)))
            # Receive timeout in seconds.
            # This has to be done after opening the connection to avoid
            # connect() error on non-blocking socket, but before starting
            # connection listener which uses this timeout for socket recv().
            # Zero sets the socket to non-blocking mode. Non-blocking mode does
            # not provide any performance benefit compared to blocking socket
            # with small delay, but it makes it to raise platform-specific
            # exceptions which might be trickier to catch.
            self._connection.settimeout(self.receive_timeout)
            self._connection_close_requested.clear()
            self.listener = threading.Thread(target=self.connection_listener, name="{}_listener".format(__name__), daemon=True)
            self.listener.start()
            self.logger.info("Opened connection to <%s:%s>", self.address, self.port)
        except TimeoutError as e:
            raise PLConnectionTimeoutError(f"Remote host {self.address}:{self.port} doesn't respond!") from e
        except (OSError, TypeError) as e:
            raise PLConnectionError(f"Can't open {self.protocol} socket for {self.address}:{self.port}!") from e

    def connection_listener(self):
        """Periodically checks for new data on the connection,
        reads it, puts it into receive buffer and raises data ready flag.
        """

        self.logger.info("Starting connection listener...")
        while True:
            # Check connection close request
            if self._connection_close_requested.is_set():
                # Clear the flag and exit
                self._connection_close_requested.clear()
                self.logger.info("Connection listener exiting.")
                return
            # Lock connection object
            with self._connection_lock:
                # Try read from socket
                try:
                    # This either gives data back or timeouts after
                    # self.receive_timeout seconds
                    chunk = self._connection.recv(self.receive_buffer_size)
                    # If there's any data, clear buffer
                    if chunk:
                        # If the flag is still set it means receive()
                        # hasn't yet read it out
                        if self._data_ready.is_set() is True:
                            self.logger.warning("Discarding unconsumed device reply <%r>", self._last_reply)
                        self._last_reply = ""
                        try:
                            while chunk:
                                self.logger.debug("connection_listener()::decoding chunk <%s>", chunk)
                                self._last_reply += chunk.decode(self.encoding)
                                chunk = self._connection.recv(self.receive_buffer_size)
                        # Socket.timeout is raised for blocking sockets after timeout
                        # BlockingIOError is raised for non-blocking sockets
                        # both on Windows and Linux
                        except (socket.timeout, BlockingIOError):
                            # Finished reading data from the socket
                            self._data_ready.set()
                        except UnicodeDecodeError:
                            self.logger.exception("Can't decode packet <%s>!", chunk, exc_info=True)
                except (socket.timeout, BlockingIOError):
                    # No data in socket
                    pass
                except ConnectionAbortedError:
                    raise PLConnectionError("Device disconnected!") from None
            # Release the lock and sleep
            sleep(self.receiving_interval)

    def close_connection(self):
        """Closes connection.
        """

        if self.is_connection_open():
            self._connection_close_requested.set()
            # There are two blocking calls in the listener loop
            # receive_timeout determines for how long it blocks on the socket to read
            # receiving_interval determines for how long it sleeps between socket reads
            self.listener.join(timeout=max(self.receiving_interval, self.receive_timeout) * 5)
            self._connection.close()
            self.logger.info("Connection to <%s:%s> closed.", self.address, self.port)
        else:
            self.logger.warning("Trying to close socket that is not open.")

    def is_connection_open(self):
        """Checks whether the socket is open

        Returns:
            (bool): If the socket is open.
        """

        if self._connection is None:
            return False
        # There's no general way in Python to check whether the socket is active.
        # This code was checked to work on Windows
        # It tries to get the connection state by checking
        # socket._closed attribute & probing with recv(1) on socket
        if not sys.platform.startswith("win"):
            raise NotImplementedError("This code was tested on Windows only!")
        if getattr(self._connection, "_closed", False) is True:
            # Socket was opened before, but now is closed
            return False
        # Otherwise socket has either been just created & connection not opened
        # or socket.connect() has been called, but connection is dead
        try:
            self._connection.recv(1)
        except socket.timeout:
            return True
        except OSError:
            return False
        return True

    def transmit(self, msg: str):
        """Sends message to the socket.
        """

        # Check if connection is alive
        if not self.is_connection_open():
            raise PLConnectionError("No connection to the device!")
        try:
            command = msg.encode(self.encoding)
        except SyntaxError:
            raise PLConnectionProtocolError("Can't encode command <{}> to a byte-string!".format(msg)) from None
        # Calculate if we have to wait after the previous command was sent
        delta = time() - self._last_command_time
        if delta < self.command_delay:
            self.logger.debug("Command rate too high! Delaying next command for <%s> seconds", self.command_delay)
            sleep(self.command_delay - delta)
        if self._data_ready.is_set() is True:
            self.logger.warning("Previous reply <%r> has not been read.", self._last_reply)
        with self._connection_lock:
            self._connection.send(command)
        self._last_command_time = time()
        self.logger.debug("transmit()::sent command <%s>", command)

    def receive(self, retries: int = 3):
        """Gets the data from receive buffer, clears the data ready flag
        and passes the data back.

        Args:
            retries (int): Number of times to retry if receive times out.
                Introduced due to RCTDigitalHotplate test showing that around
                0.02 % of attempted `get_temperature` calls timeout. These are
                spaced out and not all happening at once so 1 retry should be
                sufficient to protect against these anomalies and prevent
                unnecessary crashes.

        Returns:
            (LabDeviceReply): Reply from the device packed into LabDeviceReply object.

        """

        if not self._data_ready.is_set():
            self.logger.debug("receive()::waiting for incoming data to become ready...")
            failed_attempts = 0
            # Timeout here ensures upper level code wouldn't block forever
            # if no reply is received. It has to be long enough to give time
            # for connection_listener() thread to do it's job
            while self._data_ready.wait(timeout=self.receive_timeout * 50) is False:
                failed_attempts += 1
                if failed_attempts > retries:
                    # No reply after timeout
                    raise PLConnectionTimeoutError("No reply received from the device!")

        # Unset data ready flag
        self._data_ready.clear()
        return LabDeviceReply(body=self._last_reply, content_type="chunked")


class HTTPConnection(AbstractConnection):
    """HTTP REST connection adapter based on Requests library.
    """

    HTTP_DEFAULT_CONNECTION_PARAMETERS = {
        "user": None,
        "password": None,
        "schema": "http",
        "verify_ssl": True,
        "headers": ""
    }  # type: ConnectionParameters

    def __init__(self, connection_parameters: ConnectionParameters):
        """
        Args:
            connection_parameters (Dict): Dictionary with connection settings for HTTP REST connection.
        """

        # Init base class, set common parameters
        config = {**self.HTTP_DEFAULT_CONNECTION_PARAMETERS, **connection_parameters}
        super().__init__(config)

        # Reply for HTTP response
        self._last_reply = ""
        self._last_reply_headers = {}  # type: ignore

        # Default HTTP connection settings
        self.user = self.connection_parameters["user"]
        self.password = self.connection_parameters["password"]
        self.schema = self.connection_parameters["schema"]
        self.verify_ssl = self.connection_parameters["verify_ssl"]
        self.headers = self.connection_parameters["headers"]
        # Address settings
        self.address = self.connection_parameters["address"] + ":" + str(connection_parameters["port"])

        # Append / to host address
        if not self.address.endswith("/"):
            self.address += "/"
        # Strip :// from schema, if present
        self.schema = self.schema.strip("/")
        self.schema = self.schema.strip(":")

        # Make base URL
        self.base_url = self.schema + "://" + self.address
        self.logger.debug("HTTPConnection.__init__()::constructed base URL <%s>", self.base_url)

    def open_connection(self):
        """Creates requests.Session() object & sets it's parameters.
        """

        self._connection = requests.Session()
        if self.user is not None:
            self._connection.auth = (self.user, self.password)
        self._connection.verify = self.verify_ssl
        self._connection.headers = self.headers
        self.logger.info("Session to <%s> initialized.", self.base_url)

    def close_connection(self):
        """Closes connection.
        """

        self._connection.close()
        self.logger.info("Session to <%s> closed.", self.base_url)

    def transmit(self, message: Dict):  # type: ignore
        """Sends request to the server.

        Args:
            message: Dictionary containing method, endpoint and request data
        """

        # Make complete URL from base API URL and endpoint
        url = urljoin(self.base_url, message["endpoint"])
        self.logger.debug("transmit()::trying to invoke <%s> with method <%s>, data=<%s>", url, message["method"], message["data"])
        try:
            reply = self._connection.request(method=message["method"].upper(), url=url, data=message["data"], timeout=self.transmit_timeout)
        except requests.exceptions.Timeout as e:
            raise PLConnectionTimeoutError("Can't connect to host!") from e
        # Log headers
        self.logger.debug("transmit()::reply headers::<%r>", reply.headers)
        # Check HTTP reply code
        if reply.status_code > 400:
            raise PLConnectionProtocolError(f"Server replied with HTTP code {reply.status_code} ({reply.text})")
        self._last_reply = reply.content
        self._last_reply_headers = dict(reply.headers)

    def receive(self):
        """Passes the request response back.

        Returns:
            (LabDeviceReply): HTTP reply from the device packed into LabDeviceReply object together with reply headers.

        """
        try:
            self._last_reply = self._last_reply.decode()
        except UnicodeDecodeError:
            raise PLConnectionProtocolError(f"Can't decode device reply!\n {self._last_reply}")
        return LabDeviceReply(body=self._last_reply, parameters=self._last_reply_headers, content_type="json")

    def is_connection_open(self):
        """ Dummy method as REST is stateless.
        """
        return True
