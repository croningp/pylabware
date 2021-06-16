"""PyLabware driver for IKA RET Control Visc stirring hotplate."""

from typing import Optional, Union
import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractHotplate, in_simulation_device_returns
from ..exceptions import PLConnectionError, PLDeviceCommandError
from ..models import LabDeviceCommands, ConnectionParameters


class RETControlViscHotplateCommands(LabDeviceCommands):
    """Collection of commands for IKA RET Control Visc stirring hotplate.
    """

    # ##########################  Constants ##################################
    # Default reply to GET_NAME command
    DEFAULT_NAME = "IKARET"
    # Temperature probes
    TEMP_SENSORS = {0: "INTERNAL", 1: "EXTERNAL", 2: "MEDIUM"}

    # ################### Control commands ###################################
    # Get device name
    GET_NAME = {"name": "IN_NAME", "reply": {"type": str}}
    # Set device name, 6 symbols max
    SET_NAME = {"name": "OUT_NAME", "type": str}
    # Get internal hotplate sensor temperature
    GET_TEMP = {"name": "IN_PV_2", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get external sensor temperature
    GET_TEMP_EXT = {"name": "IN_PV_1", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get second external sensor temperature (heat carrier temperature, see the manual)
    GET_TEMP_EXT_2 = {"name": "IN_PV_7", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get hotplate safety temperature
    GET_TEMP_SAFE = {"name": "IN_PV_3", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get current stirring speed
    GET_SPEED = {"name": "IN_PV_4", "reply": {"type": int, "parser": parser.slicer, "args": [-2]}}
    # Get viscosity trend value
    GET_VISC = {"name": "IN_PV_5", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get pH value
    GET_PH = {"name": "IN_PV_80", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get weight value
    GET_WEIGHT = {"name": "IN_PV_90", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get temperature setpoint
    GET_TEMP_SET = {"name": "IN_SP_2", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get external temperature setpoint
    GET_TEMP_EXT_SET = {"name": "IN_SP_1", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get second external temperature setpoint
    GET_TEMP_EXT_2_SET = {"name": "IN_SP_7", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get safety temperature setpoint
    GET_TEMP_SAFE_SET = {"name": "IN_SP_3", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get stirring speed setpoint
    GET_SPEED_SET = {"name": "IN_SP_4", "reply": {"type": int, "parser": parser.slicer, "args": [-2]}}
    # Set temperature
    SET_TEMP = {"name": "OUT_SP_2", "type": int, "check": {"min": 0, "max": 340}}
    # Set external sensor temperature
    SET_TEMP_EXT = {"name": "OUT_SP_1", "type": int, "check": {"min": 0, "max": 340}}
    # Set second external sensor temperature
    SET_TEMP_EXT_2 = {"name": "OUT_SP_7", "type": int, "check": {"min": 20, "max": 340}}
    # Set stirring speed
    SET_SPEED = {"name": "OUT_SP_4", "type": int, "check": {"min": 50, "max": 1700}}

    # Start the heater
    START_HEAT = {"name": "START_1"}
    # Stop the heater
    STOP_HEAT = {"name": "STOP_1"}
    # Start the stirrer
    START_STIR = {"name": "START_4"}
    # Stop the stirrer
    STOP_STIR = {"name": "STOP_4"}

    # ################### Configuration commands #############################
    # Get firmware version
    GET_VERSION = {"name": "IN_VERSION", "reply": {"type": str}}
    # Reset device operation mode
    RESET = {"name": "RESET"}
    # Set watchdog fallback temperature
    SET_WD_SAFE_TEMP = {"name": "OUT_SP_12@", "type": int, "check": {"min": 0, "max": 340},
                        "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set watchdog fallback speed
    SET_WD_SAFE_SPEED = {"name": "OUT_SP_42@", "type": int, "check": {"min": 0, "max": 1700},
                         "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set timeout (seconds) and enable watchdog mode 1 (switching off on watchdog interrupt)
    SET_WD_MODE_1 = {"name": "OUT_SP_WD1@", "type": int, "check": {"min": 20, "max": 1500}}
    # Set timeout (seconds) and enable watchdog mode 2 (falling back to safety settings on watchdog interrupt)
    SET_WD_MODE_2 = {"name": "OUT_SP_WD2@", "type": int, "check": {"min": 20, "max": 1500}}
    # Set safety sensor error timeout
    # Get sensor error timeout
    GET_SENSOR_TIMEOUT = {"name": "IN_SP_54", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Set sensor error timeout
    # The user can set a value from 1 to 30 min for this time limit depending on the application. 0 -> disabled
    SET_SENSOR_TIMEOUT = {"name": "OUT_SP_54", "type": int, "check": {"min": 0, "max": 30}}
    # Set intermittent mode on time, seconds
    SET_CYCLE_ON_TIME = {"name": "OUT_SP_55", "type": int, "check": {"min": 10, "max": 600}}
    # Set intermittent mode off time, seconds
    SET_CYCLE_OFF_TIME = {"name": "OUT_SP_56", "type": int, "check": {"min": 5, "max": 60}}
    # Get intermittent mode on time, seconds
    GET_CYCLE_ON_TIME = {"name": "IN_SP_55", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get intermittent mode off time, seconds
    GET_CYCLE_OFF_TIME = {"name": "IN_SP_56", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}


class RETControlViscHotplate(AbstractHotplate):
    """
    This provides a Python class for the IKA RET Control Visc hotplate
    based on the english section of the original
    operation manual 20000004159 RET control-visc_042019
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = RETControlViscHotplateCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.SEVENBITS
        connection_parameters["parity"] = serial.PARITY_EVEN

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        # This device has no command to check status
        self._heating = False
        self._stirring = False

    def initialize_device(self):
        """Resets the device.
        """

        self.send(self.cmd.RESET)

    @in_simulation_device_returns(RETControlViscHotplateCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks whether the device is connected.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False

        if reply == self.cmd.DEFAULT_NAME:
            return True
        # Check if the stirplate is likely to be an IKA RET Control Visc (based on firmware version) and rename it
        elif self.send(self.cmd.GET_VERSION)[0:3] == "110":
            self.logger.warning("is_connected()::An IKA RET hotplate with non-standard name has been detected."
                                "Ensure that the right device is connected!"
                                "The name will be now reset to default %s", self.cmd.DEFAULT_NAME)
            # Set name to default for easier identification
            self.send(self.cmd.SET_NAME, self.cmd.DEFAULT_NAME)
            return True
        else:
            return False

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
        elif sensor == 2:
            return self.send(self.cmd.GET_TEMP_EXT_2)
        else:
            raise PLDeviceCommandError(f"Invalid sensor provided! Allowed values are: {self.cmd.TEMP_SENSORS}")

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Gets desired temperature setpoint.

        Args:
            sensor (int): Specify which temperature setpoint to read.
        """

        if sensor == 0:
            return self.send(self.cmd.GET_TEMP_SET)
        elif sensor == 1:
            return self.send(self.cmd.GET_TEMP_EXT_SET)
        elif sensor == 2:
            return self.send(self.cmd.GET_TEMP_EXT_2_SET)
        else:
            raise PLDeviceCommandError(f"Invalid sensor provided! Allowed values are: {self.cmd.TEMP_SENSORS}")

    def get_safety_temperature(self) -> float:
        """Gets safety temperature sensor reading.
        """

        return self.send(self.cmd.GET_TEMP_SAFE)

    def get_safety_temperature_setpoint(self) -> float:
        """Gets safety temperature sensor setpoint.
        """
        return self.send(self.cmd.GET_TEMP_SAFE_SET)

    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets desired temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
        """

        if sensor == 0:
            self.send(self.cmd.SET_TEMP, temperature)
        elif sensor == 1:
            self.send(self.cmd.SET_TEMP_EXT, temperature)
        elif sensor == 2:
            self.send(self.cmd.SET_TEMP_EXT_2, temperature)
        else:
            raise PLDeviceCommandError(f"Invalid sensor provided! Allowed values are: {self.cmd.TEMP_SENSORS}")

    def get_speed(self) -> int:
        """Gets current stirring speed.
        """

        return self.send(self.cmd.GET_SPEED)

    def get_speed_setpoint(self) -> int:
        """Gets desired speed setpoint.
        """

        return self.send(self.cmd.GET_SPEED_SET)

    def set_speed(self, speed: int):
        """Sets the stirring speed.
        """

        self.send(self.cmd.SET_SPEED, speed)

    def get_viscosity_trend(self) -> float:
        """Gets current viscosity value.
        """

        return self.send(self.cmd.GET_VISC)

    def get_weight(self) -> float:
        """Gets weight - the hotplate has embedded weight sensor.
        """

        return self.send(self.cmd.GET_WEIGHT)

    def get_ph(self) -> float:
        """Gets pH value from external probe.
        Returns value around 14 with no probe connected.
        """
        return self.send(self.cmd.GET_PH)

    def start_watchdog_mode1(self, timeout: int):
        """This can't be cleared remotely, requires power cycle.
        """

        self.send(self.cmd.SET_WD_MODE_1, timeout)

    def setup_watchdog_mode2(self, temperature: int, speed: int):
        """This can be cleared remotely
        """

        # Set failsafe temperature
        self.send(self.cmd.SET_WD_SAFE_TEMP, temperature)
        # Set failsafe speed
        self.send(self.cmd.SET_WD_SAFE_SPEED, speed)

    def start_watchdog_mode2(self, timeout: int):
        """This doesn't display any error as advertised in the manual, just falls back to safety values
        """

        self.send(self.cmd.SET_WD_MODE_2, timeout)

    def stop_watchdog(self):
        """Clears mode2 watchdog.
        """

        self.send(self.cmd.SET_WD_MODE_1, 0)
        self.send(self.cmd.SET_WD_MODE_2, 0)
