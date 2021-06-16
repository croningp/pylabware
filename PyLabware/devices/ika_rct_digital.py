"""PyLabware driver for IKA RCT Digital stirring hotplate."""

from typing import Optional, Union
import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractHotplate, in_simulation_device_returns
from ..exceptions import PLConnectionError, PLDeviceCommandError
from ..models import LabDeviceCommands, ConnectionParameters


class RCTDigitalHotplateCommands(LabDeviceCommands):
    """Collection of command definitions for for IKA RCT Digital stirring hotplate.
    """

    # ##########################  Constants ##################################
    # Default reply to GET_NAME command
    DEFAULT_NAME = "RCT digital"
    TEMP_SENSORS = {0: "INTERNAL", 1: "EXTERNAL"}

    # ################### Control commands ###################################
    # Get device name
    GET_NAME = {"name": "IN_NAME", "reply": {"type": str}}
    # Get external sensor temperature
    GET_TEMP_EXT = {"name": "IN_PV_1", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get internal hotplate sensor temperature
    GET_TEMP = {"name": "IN_PV_2", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get current stirring speed
    GET_SPEED = {"name": "IN_PV_4", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get viscosity trend value
    GET_VISC = {"name": "IN_PV_5", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get temperature setpoint
    GET_TEMP_SET = {"name": "IN_SP_1", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get safety temperature setpoint
    GET_SAFE_TEMP_SET = {"name": "IN_SP_3", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get stirring speed setpoint
    GET_SPEED_SET = {"name": "IN_SP_4", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set temperature
    SET_TEMP = {"name": "OUT_SP_1", "type": int, "check": {"min": 20, "max": 310}}
    # Set stirring speed
    SET_SPEED = {"name": "OUT_SP_4", "type": int, "check": {"min": 0, "max": 1500}}
    # Start the heater
    START_HEAT = {"name": "START_1"}
    # Stop the heater
    STOP_HEAT = {"name": "STOP_1"}
    # Start the stirrer
    START_STIR = {"name": "START_4"}
    # Stop the stirrer
    STOP_STIR = {"name": "STOP_4"}

    # ################### Configuration commands #############################
    # Set device operation mode A (normal)
    SET_MODE_A = {"name": "SET_MODE_A"}
    # Set device operation mode B (refer to the manual)
    SET_MODE_B = {"name": "SET_MODE_B"}
    # Set device operation mode D (refer to the manual)
    SET_MODE_D = {"name": "SET_MODE_D"}
    # Reset device operation mode
    RESET = {"name": "RESET"}


class RCTDigitalHotplate(AbstractHotplate):
    """
    This provides a Python class for the IKA RCT Digital hotplate
    based on the english section of the original
    operation manual 201811_IKAPlate-Lab_A1_25002139a.
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor
        """

        # Load commands from helper class
        self.cmd = RCTDigitalHotplateCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.SEVENBITS
        connection_parameters["parity"] = serial.PARITY_EVEN

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = " \r \n"  # Note spaces! TODO check whether this is actually important
        self.reply_terminator = "\r\n"  # No spaces here
        self.args_delimiter = " "

        # This device has no command to check status
        self._heating = False
        self._stirring = False

    def initialize_device(self):
        """Set default operation mode & reset.
        """

        self.send(self.cmd.SET_MODE_A)
        self.send(self.cmd.RESET)
        self.logger.info("Device initialized.")

    @in_simulation_device_returns(RCTDigitalHotplateCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """ Check if the device is connected via GET_NAME command.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        return reply == self.cmd.DEFAULT_NAME

    def is_idle(self) -> bool:
        """Returns True if no stirring or heating is active.
        """

        if not self.is_connected():
            return False
        return not (self._heating or self._stirring)

    def get_status(self):
        """Not supported on this device.
        """

    def check_errors(self):
        """Not supported on this device.
        """

    def clear_errors(self):
        """Not supported on this device.
        """

    def start_temperature_regulation(self):
        """Starts heating.
        """

        self.send(self.cmd.START_HEAT)
        self._heating = True

    def stop_temperature_regulation(self):
        """Stops heating.
        """

        self.send(self.cmd.STOP_HEAT)
        self._heating = False

    def start_stirring(self):
        """Starts stirring.
        """

        self.send(self.cmd.START_STIR)
        self._stirring = True

    def stop_stirring(self):
        """Stops stirring.
        """

        self.send(self.cmd.STOP_STIR)
        self._stirring = False

    def get_temperature(self, sensor: int = 0) -> float:
        """Gets the actual temperature.

        Args:
            sensor (int): Specify which temperature probe to read.
        """

        if sensor == 0:
            return self.send(self.cmd.GET_TEMP)
        elif sensor == 1:
            return self.send(self.cmd.GET_TEMP_EXT)
        else:
            raise PLDeviceCommandError(f"Invalid sensor provided! Allowed values are: {self.cmd.TEMP_SENSORS}")

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Reads the current temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device uses a shared setpoint for all temperature probes.
                          Hence, this argument has no effect here.
        """

        return self.send(self.cmd.GET_TEMP_SET)

    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets the desired temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device uses a shared setpoint for all temperature probes.
                          Hence, this argument has no effect here.
        """

        self.send(self.cmd.SET_TEMP, temperature)

    def get_speed(self) -> int:
        """Gets the actual stirring speed.
        """

        return self.send(self.cmd.GET_SPEED)

    def get_speed_setpoint(self) -> int:
        """Gets desired stirring speed setpoint.
        """

        return self.send(self.cmd.GET_SPEED_SET)

    def set_speed(self, speed: int):
        """Sets desired speed.
        """

        self.send(self.cmd.SET_SPEED, speed)

    def get_viscosity_trend(self) -> float:
        """Gets current viscosity rend.
        """

        return self.send(self.cmd.GET_VISC)
