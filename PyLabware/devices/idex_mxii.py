"""PyLabware driver for IDEX MX II series six-port sample injection valve."""

from typing import Optional, Union
import time
import serial

# Core imports
from ..controllers import AbstractDistributionValve, in_simulation_device_returns
from ..exceptions import (PLConnectionError,
                          PLDeviceCommandError,
                          PLDeviceInternalError,
                          PLConnectionTimeoutError)
from ..models import LabDeviceCommands, ConnectionParameters


class IDEXMXIIValveCommands(LabDeviceCommands):
    """Collection of command definitions for for IDEX valve controller USB protocol.
    """
    # ##########################  Constants ##################################
    # Status codes
    STATUS_CODES = {
        "*": "Busy",
        "44": "Data CRC error.",
        "55": "Data integrity error.",
        "66": "Valve positioning error.",
        "77": "Valve configuration error or command error.",
        "88": "Non-volatile memory error.",
        "99": "Valve cannot be homed."
    }
    # Separate literal for busy status, for ease of manipulation
    STATUS_BUSY = "*"

    # Command modes for external input
    COMMAND_MODES = {
        1: "Level logic",
        2: "Single pulse logic",
        3: "BCD logic",
        4: "Inverted BCD logic",
        5: "Dual pulse logic"
    }

    # Serial baudrates
    UART_BAUDRATES = {
        1: 9600,
        2: 19200,
        3: 38400,
        4: 57600
    }

    # ################### Control commands ###################################
    # Move to position
    # TODO think about casting to int & formatting
    MOVE_TO_POSITION = {"name": "P", "type": str, "reply": {"type": str}}
    # Move to home position
    MOVE_HOME = {"name": "M", "reply": {"type": str}}
    # Get status - current valve position or error code if any
    GET_STATUS = {"name": "S", "reply": {"type": str}}
    # Get last error code - not sure what's the difference between this one and the one above
    GET_ERROR = {"name": "E", "reply": {"type": int}}

    # ################### Configuration commands #############################
    # Set valve profile
    # Note: The new operational mode becomes active after
    # driver board reset. Invalid operational mode will cause error 77 (valve
    # configuration error).
    SET_VALVE_PROFILE = {"name": "O", "type": int, "check": {"min": 0, "max": 0xFF}}
    # Get valve profile
    GET_VALVE_PROFILE = {"name": "Q", "reply": {"type": int}}
    # Set new I2C address. Only even numbers.
    SET_I2C_ADDRESS = {"name": "N", "type": int, "check": {"min": 0x0E, "max": 0xFE}}
    # Set valve command mode
    SET_CMD_MODE = {"name": "F", "type": int, "check": {"values": COMMAND_MODES}}
    # Get valve command mode
    GET_CMD_MODE = {"name": "D", "type": int, "reply": {"type": int}}
    # Set baudrate
    SET_BAUDRATE = {"name": "X", "type": int, "check": {"values": UART_BAUDRATES}}
    # Get FW revision
    GET_FW_REV = {"name": "R", "reply": {"type": int}}


class IDEXMXIIValve(AbstractDistributionValve):
    """Two-position IDEX MX Series II HPLC valve."""

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = IDEXMXIIValveCommands
        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 19200
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r"
        self.reply_terminator = "\r"
        self.args_delimiter = ""

    def initialize_device(self):
        """Not supported on this device.
        """

    @in_simulation_device_returns("01")
    def is_connected(self) -> bool:
        """Checks if device is connected.
        """

        try:
            status = self.send(self.cmd.GET_FW_REV)
            # Should return integer
            if not status:
                return False
        except PLConnectionError:
            return False
        return True

    def is_idle(self):
        """Checks whether device is idle.
        """
        return self.get_status() != self.cmd.STATUS_BUSY

    def get_status(self):
        """Returns device status.
        """
        return self.send(self.cmd.GET_STATUS)

    def check_errors(self):
        """Check device for errors & raises PLDeviceInternalError with
        appropriate error message.
        """

        status = self.get_status()
        if status in self.cmd.STATUS_CODES and status != self.cmd.STATUS_BUSY:
            errmsg = self.cmd.STATUS_CODES[status]
            self.logger.error(errmsg)
            raise PLDeviceInternalError(errmsg)

    def clear_errors(self):
        """Not supported on this device.
        """

    def start(self):
        """Not supported on this device.
        """

    def stop(self):
        """Not supported on this device.
        """

    def move_home(self):
        """Move valve to home position.
        """

        self.send(self.cmd.MOVE_HOME)

    def set_valve_position(self, position: int):
        """Move value to specified position.
        Position 1 corresponds to the home position, i.e. injected sample goes
        to the loop and eluent to waste.
        Position 2 corresponds usually represents the beginning of acquisition
        where sample in the loop goes to analysis.
        """

        # This device replies \r if all OK, or nothing if the command is wrong
        # We need to distinguish that from lost connection
        # Don't forget zero padding
        try:
            self.send(self.cmd.MOVE_TO_POSITION, f"{position:02d}")
        except PLConnectionTimeoutError:
            if self.is_connected:
                raise PLDeviceCommandError(f"Wrong valve position {position}")
            else:
                raise

    def get_valve_position(self):
        """ Gets current valve position.
        """
        return self.get_status()

    def sample(self, seconds: int):
        """Move valve to position 2 for `seconds`, then switch back to 1.

        Args:
            seconds (int): Number of seconds to stay in position 2.
        """

        self.set_valve_position(2)
        time.sleep(seconds)
        self.set_valve_position(1)
