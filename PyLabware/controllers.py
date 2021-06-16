"""PyLabware device controllers."""

import copy
import logging
import threading
from abc import abstractmethod, ABC
from functools import wraps
import queue
from time import sleep
from typing import Optional, Union, Callable, Any, List, Dict, Tuple

from .connections import (HTTPConnection, SerialConnection, TCPIPConnection)
from .exceptions import (PLConnectionError, PLConnectionTimeoutError, PLDeviceError, PLDeviceCommandError, PLDeviceReplyError)
from .models import (AbstractLabDevice, ConnectionParameters)
from . import parsers as parser


def in_simulation_device_returns(value):
    """ Decorator that patched the device send() method
    to return the value passed.
    """
    def wrapper(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            # Extract object to patch from self argument
            # Self is always passed first
            slf = args[0]
            nonlocal value
            # Make a copy so that the original decorator argument won't get
            # mutated between the calls. Important if value is a placeholder
            # (see below)
            dec_retval = copy.copy(value)
            simulation = getattr(slf, "simulation", False)
            if simulation is True:
                # Find the value that we need to return. In most cases that would be
                # a decorator argument. However, in particularly pesky cases the
                # wrapped function would expect to read back one of it's arguments.
                # To implement that, {$args[<number>]} string as decorator argument
                # is treated specially.
                try:
                    if "{$args[" in value:
                        # Try to find positional argument number for the wrapped
                        # method call that we want to use as return value by inspecting
                        # the decorator arguments
                        argnum = value[value.find("[") + 1:value.find("]")]
                        try:
                            argnum = int(argnum)
                        except ValueError:
                            slf.logger.error("SIM:: Can't extract argument number from {$args[]}, check syntax!")
                            dec_retval = None
                        try:
                            # Get the actual wrapped method argument from the list
                            dec_retval = args[argnum]
                        except IndexError:
                            slf.logger.error("SIM:: Can't find argument number %s in arguments list <%s>!", value, args)
                            dec_retval = None
                except TypeError:
                    # value is non-iterable
                    pass
                # Save reference to original send()
                orig_send = slf.send
                # Replace it with lambda returning the value we want - either a
                # static decorator argument or dynamic value from the wrapped
                # function call syntax
                slf.send = lambda *a, **k: dec_retval
                slf.logger.info("SIM :: Patched send() to return <%s>, calling <%s>", value, func.__name__)
                # Get return value (if any) for the actual function - other
                # functions in the call chain may rely on it
                retval = func(*args, **kwargs)
                # Restore original send() back
                slf.send = orig_send
                return retval
            # No simulation - return original function
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper


class LabDevice(AbstractLabDevice):
    """Base controller class for all labware devices.
    """

    @abstractmethod
    def __init__(self, device_name: str = None, connection_mode: str = None,
                 connection_parameters: ConnectionParameters = None):
        """Default constructor. This function performs object initialization.
        All device-specific hardware initialization procedures should be inside
        the :py:meth:`~PyLabware.models.AbstractLabDevice.initialise_device()` method.

        This method has to be redefined in child classes.

        Args:
            device_name: Device name (for logging purposes).
            connection_mode: Physical connection mode (defines the connection
                             adapter used).
            connection_parameters: Dictionary with connection-specific settings.
                                   These vary depending on the connection_mode.
        """

        # Instance name
        if device_name is None:
            device_name = self.__class__.__name__
        self.device_name = device_name

        # Logger object
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__ + "." + self.device_name)

        # Flags
        self._simulation = False

        # Lock object for thread-safe access to connection object
        self._lock = threading.RLock()
        # Pool of threads for keepalive/background tasks
        self._background_tasks: List[LabDeviceTask] = []

        # Protocol settings
        self.command_prefix = ""
        self.command_terminator = "\r\n"
        # Delimiter between the command and argument(s list)
        self.args_delimiter = " "
        self.reply_prefix = ""
        self.reply_terminator = "\r\n"

        if connection_parameters is None:
            connection_parameters = {}

        # Choose & instantiate right connection object
        if connection_mode == "serial":
            self.connection = SerialConnection(connection_parameters)
        elif connection_mode == "tcpip":
            self.connection = TCPIPConnection(connection_parameters)
        elif connection_mode == "http":
            self.connection = HTTPConnection(connection_parameters)
        else:
            raise PLDeviceError(f"Unsupported connection mode <{connection_mode}> for <{self.device_name}>")

    @property
    def simulation(self) -> bool:
        """ Determines whether the device behaves as as a real or simulated one.
            Simulated device just logs all the commands.
        """

        return self._simulation

    @simulation.setter
    def simulation(self, sim: bool):
        """ Setter for the simulation property
        """

        self._simulation = bool(sim)

    def connect(self):
        """ Connects to the device.

        This method normally shouldn't be redefined in child classes.
        """

        if self._simulation is True:
            self.logger.info("SIM :: Opened connection.")
            return
        try:
            self.connection.open_connection()
        except (PLConnectionError, PLConnectionTimeoutError) as e:
            raise PLDeviceError(f"Can't connect to device <{self.__class__.__name__}.{self.device_name}>!") from e
        self.logger.info("Opened connection.")

    def disconnect(self):
        """ Disconnects from the device.

        This method normally shouldn't be redefined in child classes.
        """

        if self._simulation is True:
            self.logger.info("SIM :: Closed connection")
            return
        # Stop all background tasks if any
        if self._background_tasks:
            self.logger.info("Background tasks running, stopping them before disconnect.")
            self.stop_all_tasks()
        self.connection.close_connection()
        self.logger.info("Closed connection.")

    def send(self, cmd, value=None):
        """This method takes the command to be sent and runs all necessary
        checks on the command parameter if present and required. Then the
        command get wrapped with the necessary prefix/terminator and connection
        lock is acquired. The command string is sent to the device using
        appropriate connection adapter and _recv() is invoked if a reply is
        expected. Only after that the connection lock is released.

        This method normally shouldn't be redefined in child classes.

        Args:
            cmd: The command to send.
            value: Command parameter, if any.
        """

        if value is not None:
            value = self.check_value(cmd, value)

        message = self.prepare_message(cmd, value)

        if self._simulation is True:
            self.logger.info("SIM :: Pretending to send message <%r>", message)
            return None

        # Check if we need to get reply back for this command
        reply_expected = cmd.get("reply", False)

        with self._lock:
            self.connection.transmit(message)
            self.logger.debug("Sent message <%r>", message)
            if reply_expected:
                return self._recv(cmd)

    def check_value(self, cmd: Dict, value: Any) -> Any:
        """ Checks the value provided against the definitions in command dict.
        Then does any value conversion/formatting/type casting as needed.

        This method may be redefined in child classes.

        Args:
            cmd: Device command definition.
            value: Command parameter to check.

        Returns:
            (Any): Processed value.
        """

        # Value type casting
        # TODO think about moving type to check dictionary
        if "type" in cmd.keys() and cmd["type"] is not None:
            try:
                value = cmd["type"](value)
                self.logger.debug("check_value()::type casted value <%s> to <%s>.", value, cmd["type"])
            # Invalid type definition
            except TypeError:
                self.logger.error("check_value()::Illegal type <%s> specification in command <%s> definition.", cmd["type"], cmd["name"])
            # Type cast error
            except ValueError:
                raise PLDeviceCommandError(f"Can't cast value <{value}> to type <{cmd['type']}>.")
        else:
            self.logger.debug("check_value()::type casting not required - skipped.")

        # Check if any checking/processing is required acc. to cmd definition
        check_needed = cmd.get("check", False)
        if check_needed is False:
            return value

        # Value checking
        if "check" in cmd.keys() and cmd["check"] is not None:

            # Min/max check
            try:
                if value < cmd["check"]["min"]:
                    raise PLDeviceCommandError(f"Requested value <{value}> is below limit <{cmd['check']['min']}> !")
                self.logger.debug("check_value()::min check <%s> < <%s>", value, cmd['check']['min'])
                if value > cmd["check"]["max"]:
                    raise PLDeviceCommandError(f"Requested value <{value}> is above limit <{cmd['check']['max']}> !")
                self.logger.debug("check_value()::max check <%s> > <%s>", value, cmd['check']['max'])
            # No cmd["check"]["min"] or cmd["check"]["max"]
            except KeyError:
                self.logger.debug("check_value()::min/max check not required - skipped.")
            # Invalid value in cmd["check"]["min"] or cmd["check"]["max"]
            except TypeError:
                self.logger.error("Illegal min/max values specification in command <%s> definition!", cmd["name"])

            # Value in range check
            try:
                if value not in cmd["check"]["values"]:
                    raise PLDeviceCommandError(f"Requested value <{value}> not in the allowed range <{cmd['check']['values']}>.")
                self.logger.debug("check_value()::range check <%s> in range <%s>", value, cmd["check"]["values"])
            # No cmd["check"]["range"]
            except KeyError:
                self.logger.debug("check_value()::range check not required - skipped.")
            except TypeError:
                self.logger.error("Illegal range specification in command <%s> definition.", cmd["name"])
        return value

    def prepare_message(self, cmd: Dict, value: Any) -> str:
        """This function does all preparations needed to make the command
        compliant with device protocol, e.g. type casts the parameters, checks
        that their values are in range, adds termination sequences, etc.

        This method may be redefined in child classes.

        Args:
            cmd: Device command definition.
            value: Command parameter to set, if any.

        Returns:
            (str): Checked & prepared command string.
        """

        if value is None:
            return self.command_prefix + cmd["name"] + self.command_terminator
        # Else
        return self.command_prefix + cmd["name"] + self.args_delimiter + str(value) + self.command_terminator

    def _recv(self, cmd: Dict) -> Union[int, float, str, bool]:
        """Locks the connection object, reads back the reply and re-assembles it
        if it is chunked. Then parses the reply if necessary and passes it back.

        This method normally shouldn't be redefined in child classes.

        Args:
            parse: If reply parsing is required.

        Returns:
            (str): Reply from the device.
        """

        if self.simulation is True:
            self.logger.info("SIM :: Received reply.")
            return ""
        with self._lock:
            reply = self.connection.receive()
            # Check if we got complete reply in case it is chunked
            # If not, keep reading out data until the terminator
            # TODO how (any) parameters should be appended to reply object?
            if reply.content_type == "chunked":
                if self.reply_terminator is not None or self.reply_terminator != "":
                    while not reply.body.endswith(self.reply_terminator):
                        self.logger.debug("_recv()::reply terminator not found, reading next chunk.")
                        reply_chunk = self.connection.receive()
                        reply.body = reply.body + reply_chunk.body
                else:
                    self.logger.warning("Received chunked reply, but reply terminator is not set - reassembly not possible!")
        self.logger.debug("Raw reply from the device: <%r>", reply.body)

        # Usually, we don't expect empty replies when we are waiting for them
        if reply.body == "":
            self.logger.warning("Empty reply from device!")

        # Run parsing
        reply = self.parse_reply(cmd, reply)

        # Run type casting
        # This would work properly only between base Python types
        if not isinstance(reply, (int, float, str, bool)):
            self.logger.debug("cast_reply_type()::complex data type <%s>, skipping casting.", type(reply))
            return reply
        return self.cast_reply_type(cmd, reply)

    def parse_reply(self, cmd: Dict, reply: Any) -> Any:
        """This function takes a LabDeviceReply object and does all necessary
        processing to return a reply string back. Parsing is done according to
        command specification.

        This method may be redefined in child classes.

        Args:
            reply: Reply from the device
            cmd: Command definition to look the parsing workflow in.

        Returns:
            (any): Processed reply
        """

        # The condition below is always True unless parse_reply()
        # has been redefined in the child class and this is being executed
        # in a super() call after the actual string has already been extracted
        # from the LabDeviceReply object.
        try:
            reply = reply.body
        except AttributeError:
            pass

        # Always strip off prefix and terminator before proceeding
        reply = parser.stripper(reply, self.reply_prefix, self.reply_terminator)

        # Get parser function
        try:
            function = cmd["reply"]["parser"]
            # Then get parser function arguments
            args = cmd["reply"].get("args", [])
            self.logger.debug("parse_reply()::got parser <%s>, arguments <%s>", function, args)
            # Run parsing
            if callable(function):
                reply = function(reply, *args)
                self.logger.debug("parse_reply()::parsed reply <%s>", reply)
            else:
                self.logger.error("Parsing function <%s> defined for command <%s> is not callable!", function, cmd["name"])
        except KeyError:
            # No parser found in command definition
            self.logger.debug("parse_reply()::parsing not defined for command <%s> - skipped.", cmd["name"])

        return reply

    def cast_reply_type(self, cmd: Dict, reply: Any) -> Union[int, float, str, bool]:
        """Casts reply type based on the type provided in command definition.

        Args:
            reply: Reply string.
            cmd: Command definition to look the type value in.

        Returns:
            (any): Reply casted to the correct type.
        """

        try:
            # Special case - "0" string should be casted to boolean False
            if reply == "0" and cmd["reply"]["type"] is bool:
                casted_reply = False
            # Special case - returned value is a string representing float (e.g.
            # "0.0") and we need to cast it to int. int("0.0") would give a
            # ValueError, so we need to convert it to float first
            if cmd["reply"]["type"] is int:
                casted_reply = int(float(reply))
            else:
                casted_reply = cmd["reply"]["type"](reply)
            self.logger.debug("cast_reply_type()::casted reply type to %s.", cmd['reply']['type'])
        # No cmd["reply"]["type"] node found
        except KeyError:
            self.logger.debug("cast_reply_type()::no type definition found - skipped.")
            return reply
        # cmd["reply"]["type"] does not point to a proper data type
        except TypeError:
            self.logger.error("Illegal parse type <%s> specification in command <%s> definition.", cmd["reply"]["type"], cmd["name"])
            return reply
        # Type casting error
        except ValueError:
            raise PLDeviceReplyError(f"Can't cast reply <{reply}> to type <{cmd['reply']['type']}>.")
        else:
            return casted_reply

    def wait_until_ready(self, check_ready: Optional[Callable] = None):
        """Acquires device lock, waits till device is ready and returns.
        If no method is provided for checking, self._is_idle is used.

        Args:
            check_ready: A method to use for checking whether the device is ready or not.
        """
        return self.execute_when_ready(action=lambda *args: None, check_ready=check_ready)

    def execute_when_ready(self, action: Callable, *args, check_ready: Optional[Callable] = None):
        """Acquires device lock, waits till device is ready and runs specified
        action. If no method is provided for checking, :py:meth:`PyLabware.models.AbstractLabDevice._is_idle` is used.

        Parameters:
                 action: A method to run when the device is ready
                   args: List of positional arguments for the method to run
            check_ready: A method to use for checking whether the device is ready or not. (keyword-only)

        Returns:
            (any): The return value of action.
        """
        with self._lock:
            if check_ready is None:
                check_ready = self.is_idle
            while not check_ready():
                sleep(0.5)
            self.logger.info("Waiting done. Device <%s> ready.", self.device_name)
            if args is not None:
                return action(*args)
            else:
                return action()

    def start_task(self, interval: int, method: Callable, args=None):
        """Creates a LabDeviceTask object, starts it and appends the reference
        to the task instance to the list of tasks.

        Args:
            interval: How often the method should be executed, in seconds
            method: The function to run.
            args: Arguments for the function, if any.

        Returns:
            (LabDeviceTask): Created task object for further reference.
        """

        # Prepare task object
        task = LabDeviceTask(interval, method, args)
        self.logger.info("Starting background task for <%s(%s)>", method.__name__, args)
        task.start()
        self._background_tasks.append(task)
        return task

    def stop_task(self, task_to_stop=None):
        """Stops the LabDeviceTask object and remove the reference to it
        from the list of tasks. If no argument is provided and only a single
        task is running - stops that one.

        Arg:
            task_to_stop: LabDeviceTask object to stop.
        """

        # If there's only a single task thread & no arguments - stop it
        if task_to_stop is None and len(self._background_tasks) == 1:
            self._background_tasks[0].stop()
            return
        if task_to_stop is None:
            self.logger.error("More than one task present, don't know which to stop!")
            return
        for task in self._background_tasks:
            if task == task_to_stop:
                self.logger.info("Stopping task thread <%s>.", task.ident)
                task.stop()
                task.join(task.interval)
                self._background_tasks.remove(task)
                return
        self.logger.error("Task %s not found!", task_to_stop)

    def stop_all_tasks(self):
        """Stops all tasks currently running and resets internal list of tasks.
        """

        for task in self._background_tasks:
            self.logger.info("Stopping background task <%s>.", task.ident)
            task.stop()
            task.join(task.interval)
        self._background_tasks = []

    def get_all_tasks(self):
        """Returns internal list of tasks.
        """

        return self._background_tasks


class LabDeviceTask(threading.Thread):
    """Simple class to implement periodically running device actions."""

    def __init__(self, interval: int, method: Callable, args=None):
        """Default constructor"""

        super().__init__()

        self.interval = interval
        self.method = method
        self.results = queue.Queue(maxsize=100)
        # Kill all tasks upon exit
        self.daemon = True
        self.args = args if args is not None else []

        # Stop flag
        self._stop_requested = threading.Event()

        # Logger object
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__ + "." + self.method.__name__)

    def run(self):
        """Starts task activity."""

        self.logger.info("Background task %s started. Executing <%s> command every <%s> seconds.", threading.get_ident(), self.method.__name__, self.interval)
        while not self._stop_requested.is_set():
            retval = self.method(*self.args)
            if retval is not None:
                try:
                    self.results.put(retval)
                except queue.Full:
                    self.logger.warning("Can't push background task return value <%s> into the queue. The queue is full!", retval)
            self._stop_requested.wait(self.interval)
        self.logger.info("Background task <%s> exiting.", threading.get_ident())

    def stop(self):
        """Sets the stop flag to signal for the thread to exit."""

        self._stop_requested.set()


# ############## Base abstract controller classes ###############


class AbstractTemperatureController(LabDevice):
    """Any device capable of heating or cooling with temperature regulation."""

    @abstractmethod
    def start_temperature_regulation(self) -> None:
        """Starts temperature regulation."""

    def start(self) -> None:
        """Starts the device"""
        return self.start_temperature_regulation()

    @abstractmethod
    def stop_temperature_regulation(self) -> None:
        """Stops temperature regulation."""

    def stop(self) -> None:
        """Stops the device."""
        return self.stop_temperature_regulation()

    @abstractmethod
    def set_temperature(self, temperature: float, sensor: int = 0) -> None:
        """Sets desired temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          Default (0) is the internal probe.
        """

    @abstractmethod
    def get_temperature(self, sensor: int = 0) -> float:
        """Gets the actual temperature.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          Default (0) is the internal probe.
        """

    @abstractmethod
    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Gets desired temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          Default (0) is the internal probe.
        """


class AbstractStirringController(LabDevice):
    """Any device capable of stirring."""

    @abstractmethod
    def start_stirring(self) -> None:
        """Starts stirring."""

    def start(self) -> None:
        """Starts the device"""
        return self.start_stirring()

    @abstractmethod
    def stop_stirring(self) -> None:
        """Stops stirring."""

    def stop(self) -> None:
        """Stops the device"""
        return self.stop_stirring()

    @abstractmethod
    def set_speed(self, speed: int) -> None:
        """Sets desired stirring speed, in RPM."""

    @abstractmethod
    def get_speed(self) -> int:
        """Gets the actual stirring speed, in RPM."""

    @abstractmethod
    def get_speed_setpoint(self) -> int:
        """Gets desired stirring speed setpoint, in RPM."""


class AbstractPressureController(LabDevice):
    """Any device capable of regulating the pressure."""

    @abstractmethod
    def start_pressure_regulation(self) -> None:
        """Starts regulating the pressure."""

    def start(self) -> None:
        """Starts the device"""
        return self.start_pressure_regulation()

    @abstractmethod
    def stop_pressure_regulation(self) -> None:
        """Stops regulating the pressure."""

    def stop(self) -> None:
        """Stops the device"""
        return self.stop_pressure_regulation()

    @abstractmethod
    def vent_on(self) -> None:
        """Vents the system to atmosphere."""

    @abstractmethod
    def vent_off(self) -> None:
        """Stops venting the system to atmosphere."""

    @abstractmethod
    def set_pressure(self, pressure: float) -> None:
        """Sets desired pressure."""

    @abstractmethod
    def get_pressure(self) -> float:
        """Gets the actual pressure"""

    @abstractmethod
    def get_pressure_setpoint(self) -> float:
        """Gets desired pressure setpoint."""


class AbstractDispensingController(LabDevice):
    """Any device capable of withdrawing and dispensing the material."""

    @abstractmethod
    def set_speed(self, speed: int) -> None:
        """Sets the dispensing speed."""

    @abstractmethod
    def get_speed(self) -> int:
        """Gets the dispensing speed."""

    @abstractmethod
    def withdraw(self, amount: int) -> None:
        """Withdraws the defined amount of material."""

    @abstractmethod
    def dispense(self, amount: int) -> None:
        """Dispenses the defined amount of material."""


class AbstractDistributionController(LabDevice):
    """An N-to-M distribution device."""

    @abstractmethod
    def move_home(self) -> None:
        """Resets the device distribution machinery to it's power on state."""

    @abstractmethod
    def connect_ports(self, port1: Any, port2: Any) -> None:
        """Makes connection between provided input and output."""

    @abstractmethod
    def disconnect_ports(self, port1: Any, port2: Any) -> None:
        """Breaks connection between provided input and output."""

    @abstractmethod
    def get_port_connections(self) -> List[Tuple]:
        """Gets a list of tuples (portX, portY) representing current connectivity."""


class AbstractDistributionValve(LabDevice):
    """A 1-to-N distribution device."""

    @abstractmethod
    def move_home(self) -> None:
        """Resets the device distribution machinery to it's power on state."""

    @abstractmethod
    def set_valve_position(self, position: Any) -> None:
        """Connects the chosen distribution valve output to its input."""

    @abstractmethod
    def get_valve_position(self) -> Any:
        """Gets currently selected distribution valve output."""


# ############## Derived abstract controller classes ###############


class AbstractHotplate(AbstractTemperatureController, AbstractStirringController, ABC):
    """A typical hotplate capable of heating and stirring simultaneously."""

    def start(self) -> None:
        """Starts the device."""
        self.start_stirring()
        self.start_temperature_regulation()

    def stop(self) -> None:
        """Stops the device"""
        self.stop_temperature_regulation()
        self.stop_stirring()


class AbstractRotavap(AbstractTemperatureController, AbstractStirringController):
    """A typical rotary evaporator, without integrated vacuum controller/pump."""

    @abstractmethod
    def lift_up(self) -> None:
        """Lifts the evaporation flask up."""

    @abstractmethod
    def lift_down(self) -> None:
        """Lowers the evaporation flask down."""

    @abstractmethod
    def start_rotation(self) -> None:
        """Human-friendly wrapper for the start_stirring() of the parent class."""

    @abstractmethod
    def stop_rotation(self) -> None:
        """Human-friendly wrapper for the stop_stirring() of the parent class."""

    def start_stirring(self) -> None:
        """Mandatory method inherited from the AbstractStirringController."""
        return self.start_rotation()

    def stop_stirring(self) -> None:
        """Mandatory method inherited from the AbstractStirringController."""
        return self.stop_rotation()

    @abstractmethod
    def start_bath(self) -> None:
        """Human-friendly wrapper for the start_temperature_regulation() of the parent class."""

    @abstractmethod
    def stop_bath(self) -> None:
        """Human-friendly wrapper for the stop_temperature_regulation() of the parent class."""

    def start_temperature_regulation(self) -> None:
        """Mandatory method inherited from the AbstractTemperatureController."""
        return self.start_bath()

    def stop_temperature_regulation(self) -> None:
        """Mandatory method inherited from the AbstractTemperatureController."""
        return self.stop_bath()


# ###################################### Derived abstract classes ##################################################


class AbstractSyringePump(AbstractDispensingController):
    """A syringe pump device."""

    @abstractmethod
    def move_home(self) -> None:
        """Moves the plunger to home position."""

    @abstractmethod
    def move_plunger_absolute(self, position: int) -> None:
        """Moves the plunger to an absolute position."""

    @abstractmethod
    def move_plunger_relative(self, position: int) -> None:
        """Moves the plunger relative +/- to the current position."""

    @abstractmethod
    def get_plunger_position(self) -> int:
        """Gets the actual plunger position."""


class AbstractFlashChromatographySystem(LabDevice):
    """ A flash chromatography system. """
