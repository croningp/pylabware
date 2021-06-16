"""PyLabware data models."""

from typing import Dict
from abc import ABC, abstractmethod


ConnectionParameters = Dict
""" Leave that till the good times come
class ConnectionParameters(TypedDict, total=False):
    address: Optional[str]
    api_url: str
    baudrate: int
    bytesize: int
    command_delay: float
    dsrdtr: bool
    encoding: str
    headers: str
    inter_byte_timeout: float
    parity: str
    password: str
    port: Union[int, str]
    protocol: str
    receiving_interval: float
    receive_timeout: float
    receive_buffer_size: int
    rtscts: bool
    schema: str
    stopbits: float
    timeout: float
    transmit_timeout: float
    user: str
    verify_ssl: bool
    xonxoff: bool
    write_timeout: float
"""


class LabDeviceCommands(ABC):
    """ This class acts as a container for all device command string
        and provides the basic features for value checking and reply parsing.
        If more advanced device-specific processing is needed
        it has to be done in device driver classes by custom parsing functions.
    """

    def __new__(cls, *args, **kwargs):
        """This class shouldn't be instantiated"""
        raise NotImplementedError


class LabDeviceReply:
    """ This class defines the data model for a device reply for all transport types (plain text, HTTP REST, ...)
    """

    __slots__ = ["body", "content_type", "parameters"]

    def __init__(self, body="", content_type="text", parameters=None):

        self.body = body
        self.content_type = content_type
        self.parameters = parameters

# ###################################### Base abstract classes ##################################################


class AbstractLabDevice(ABC):
    """Base abstract class for all labware devices.
    """

    @property
    @abstractmethod
    def simulation(self):
        """ Determines whether the device behaves as as a real or simulated one.
            Simulated device just logs all the commands.
        """

    @simulation.setter
    def simulation(self, sim):
        """ Setter for the simulation property
        """

    @abstractmethod
    def connect(self):
        """ Connects to the device.
        """

    @abstractmethod
    def disconnect(self):
        """ Disconnects from the device.
        """

    @abstractmethod
    def is_connected(self):
        """Checks if connection to the device is active.
        This method should issue a device-specific command
        (e.g. status/info command) and check the reply from the device
        to figure out whether the device is actually responsive,
        and not just returns the state of the connection itself
        (e.g. underlying connection object is_connection_open() method).

        This method has to catch all potential exceptions
        and always return either True or False.

        Returns:
            (bool): Whether device is connected or not.
        """

    @abstractmethod
    def is_idle(self):
        """Checks whether the device is in idle state.
        The idle state is defined as following:

        * The device has just been powered on AND is_connected() is True
        * OR if device has an idle status indication - if device.status == idle
        * OR if device doesn't have an idle status indication - after device.stop() was called

        This method has to execute device-specific command, if possible,
        to check whether a device is in idle state as defined above.

        If there's no command to get device status, an internal flag self._running
        has to be used.
        If the device has multiple activities (e.g. hotplate), an appropriate
        set of flags has to be used (idle == not (self._stirring or self._heating))

        This method has to catch all potential exceptions
        and always return either True or False.

        This method has to be redefined in child classes.

        Returns:
            (bool): Device ready status
        """

    @abstractmethod
    def initialize_device(self):
        """Many devices require hardware initialization before they can be used.
        This method should run hardware initialization/resetting or setting
        all the necessary parameters.

        This method has to be redefined in child classes.
        """

    @abstractmethod
    def get_status(self):
        """Gets device internal status, if implemented in the device.
        """

    @abstractmethod
    def check_errors(self):
        """Gets errors from the device (if the device supports it) and raises
        SLDeviceInternalError with error-specific message if any errors are
        present.
        """

    @abstractmethod
    def clear_errors(self):
        """Clears internal device errors, if any.
        """

    @abstractmethod
    def start(self):
        """Main method that starts device's intended activity.
        E.g if it's a stirrer, starts stirring. If it's a stirring hotplate -
        starts both stirring and heating. For granular control child classes for
        the devices capable of multiple activities (e.g. stirring hotplate)
        must implement separate methods defined in the respective derivate
        abstract classes.
        """

    @abstractmethod
    def stop(self):
        """ Stops all device activities and brings it back to idle state.
        According to the definition of is_idle() above, is_idle() ran after
        stop() must return True.
        """

    @abstractmethod
    def execute_when_ready(self, action, *args, check_ready):
        """Acquires device lock, waits till device is ready
        and runs device method.

        Args:
                 action: A function to run when the device is ready
                   args: List of arguments for the method to run
            check_ready: A method to use for checking whether
                        the device is ready or not.

        """

    @abstractmethod
    def wait_until_ready(self, check_ready):
        """Acquires device lock, waits till device is ready
        and returns.

        Args:
            check_ready: A method to use for checking whether
                        the device is ready or not.

        """
