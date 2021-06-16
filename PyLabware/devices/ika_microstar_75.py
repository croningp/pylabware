"""PyLabware driver for IKA Microstar 75 overhead stirrer."""

from typing import Optional, Union
import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractStirringController, in_simulation_device_returns
from ..exceptions import PLConnectionError
from ..models import LabDeviceCommands, ConnectionParameters


class Microstar75StirrerCommands(LabDeviceCommands):
    """Collection of command definitions for Microstar 75 overhead stirrer.
    """

    # ##########################  Constants ##################################
    # Default reply to GET_NAME command
    DEFAULT_NAME = "Microstar C"
    ROTATION_DIRECTIONS = {"IN_MODE_1": "CW", "IN_MODE_2": "CCW"}

    # ################### Control commands ###################################
    # Get device name
    GET_NAME = {"name": "IN_NAME", "reply": {"type": str}}

    # Get current stirring speed
    GET_SPEED = {"name": "IN_PV_4", "reply": {"type": int, "parser": parser.slicer, "args": [-2]}}
    # Get torque value
    GET_TORQUE = {"name": "IN_PV_5", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}

    # Get stirring speed setpoint
    GET_SPEED_SET = {"name": "IN_SP_4", "reply": {"type": int, "parser": parser.slicer, "args": [-2]}}

    # Set stirring speed
    SET_SPEED = {"name": "OUT_SP_4", "type": int, "check": {"min": 30, "max": 2000}}

    # Start the stirrer
    START = {"name": "START_4"}
    # Stop the stirrer
    STOP = {"name": "STOP_4"}

    # ################### Configuration commands #############################
    # Get internal Pt1000 reading
    GET_INT_PT1000 = {"name": "IN_PV_3", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get torque limit value
    GET_TORQUE_LIMIT = {"name": "IN_SP_5", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set torque limit value
    SET_TORQUE_LIMIT = {"name": "OUT_SP_5", "type": int}
    # Get speed limit value
    GET_SPEED_LIMIT = {"name": "IN_SP_6", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set speed limit value
    SET_SPEED_LIMIT = {"name": "OUT_SP_6", "type": int, "check": {"min": 30, "max": 2000}}
    # Get safety speed value
    GET_SPEED_SAFETY = {"name": "IN_SP_8", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get safety speed value
    SET_SPEED_SAFETY = {"name": "OUT_SP_8"}
    # Get rotation direction
    GET_ROTATION_DIR = {"name": "IN_MODE", "reply": {"type": str, "parser": parser.slicer, "args": [-1]}}
    # Set rotation direction CW
    SET_ROTATION_DIR_CW = {"name": "OUT_MODE_1", "reply": {"type": str}}
    # Set rotation direction CW
    SET_ROTATION_DIR_CCW = {"name": "OUT_MODE_2", "reply": {"type": str}}
    # Reset device operation mode
    RESET = {"name": "RESET"}


class Microstar75Stirrer(AbstractStirringController):
    """
    This provides a Python class for the Microstar 75 overhead stirrer
    based on the english section of the original operation manual
    20000008217b_EN_IKA MICROSTAR control_072019_web
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = Microstar75StirrerCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.SEVENBITS
        connection_parameters["parity"] = serial.PARITY_EVEN
        connection_parameters["command_delay"] = 0.3

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        # Internal speed variable
        # This device has a bug - if you set speed when the stirrer is off
        # It wil set the speed to zero upon start
        self._speed_setpoint = 0

        # Running flag - this device doesn't have a status check command
        self._running = False

    def initialize_device(self):
        """Performs device initialization. Updates internal variable with the
        actual speed setpoint from the device.
        """

        self.get_speed_setpoint()
        self.logger.info("Device initialized.")

    def reset(self):
        """Switches back to local control, according to the manual
        """

        self.send(self.cmd.RESET)

    @in_simulation_device_returns(Microstar75StirrerCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks whether device is connected.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        return reply == self.cmd.DEFAULT_NAME

    def is_idle(self) -> bool:
        """Checks whether device is ready.
        """

        if not self.is_connected():
            return False
        return not self._running

    def get_status(self):
        """Not supported on this device.
        """

    def check_errors(self):
        """Not supported on this device.
        """

    def clear_errors(self):
        """Not supported on this device.
        """

    def start_stirring(self):
        """Starts rotation.
        """

        self.send(self.cmd.START)
        self.set_speed(self._speed_setpoint)
        self._running = True

    def stop_stirring(self):
        """Stops rotation.
        """

        self.send(self.cmd.STOP)
        self._running = False

    def set_speed(self, speed: int):
        """Sets rotation speed.
        """

        self.send(self.cmd.SET_SPEED, speed)
        self._speed_setpoint = speed

    def get_speed(self) -> int:
        """Gets actual rotation speed.
        """

        return self.send(self.cmd.GET_SPEED)

    def get_speed_setpoint(self) -> int:
        """Gets desired rotation speed.
        """

        self._speed_setpoint = self.send(self.cmd.GET_SPEED_SET)
        return self._speed_setpoint

    def get_rotation_direction(self) -> str:
        """Gets current rotation direction.
        """

        reply = self.send(self.cmd.GET_ROTATION_DIR)
        return self.cmd.ROTATION_DIRECTIONS[reply]

    def set_rotation_direction(self, direction: str = "CW"):
        """Sets desired rotation direction - CW or CCW.
        """

        direction = direction.upper()
        if direction not in self.cmd.ROTATION_DIRECTIONS.values():
            self.logger.error("Rotation direction can be only CW or CCW")
            return
        if self.get_speed() != 0:
            self.logger.warning("Direction change is allowed only when stirrer is off.")
            return
        if direction == "CW":
            self.send(self.cmd.SET_ROTATION_DIR_CW)
        else:
            self.send(self.cmd.SET_ROTATION_DIR_CCW)

    def change_rotation_direction(self):
        """Swaps current rotation direction.
        """

        direction = self.get_rotation_direction()
        self.stop()
        if direction == "CW":
            self.send(self.cmd.SET_ROTATION_DIR_CCW)
        else:
            self.send(self.cmd.SET_ROTATION_DIR_CW)
        self.start()
