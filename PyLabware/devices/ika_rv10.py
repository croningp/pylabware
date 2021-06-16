"""PyLabware driver for IKA RV10 rotavap."""

from typing import Optional, Union
import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractRotavap, in_simulation_device_returns
from ..exceptions import PLConnectionError
from ..models import LabDeviceCommands, ConnectionParameters


class RV10RotovapCommands(LabDeviceCommands):
    """Collection of command definitions for RV10 rotavap.
    """

    # ##########################  Constants ##################################
    # Default name.
    DEFAULT_NAME = "RV10Digital"
    STATUS_CODES = {
        "0": "Manual operation",
        "1": "Remote operation",
        "E01": "No rotation",
        "E02": "No communication with the heating bath"
    }

    # Heating mediums for the bath
    HEATING_MEDIUMS = {
        0: "Oil",
        1: "Water"
    }

    # ################### Control commands ###################################
    # Get device name
    GET_NAME = {"name": "IN_NAME", "reply": {"type": str, "parser": parser.slicer, "args": [None, 11]}}
    # Get software version
    GET_VERSION = {"name": "IN_SOFTWARE", "reply": {"type": str}}
    # The lift commands in the manual are wrong. The working command was found by Sebastian Steiner by e-mailing IKA.
    # Move lift up
    LIFT_UP = {"name": "OUT_SP_62 1"}
    # Move lift down
    LIFT_DOWN = {"name": "OUT_SP_63 1"}
    # Get rotation speed
    GET_SPEED = {"name": "IN_PV_4", "reply": {"type": int, "parser": parser.slicer, "args": [None, -2]}}
    # Get rotation speed setpoint
    GET_SPEED_SET = {"name": "IN_SP_4", "reply": {"type": int, "parser": parser.slicer, "args": [None, -2]}}
    # Set rotation speed
    SET_SPEED = {"name": "OUT_SP_4", "type": int, "check": {"min": 0, "max": 280}}
    # Start rotation
    START_ROTATION = {"name": "START_4"}
    # Stop rotation
    STOP_ROTATION = {"name": "STOP_4"}
    # Start interval mode
    START_INTERVAL = {"name": "START_60"}
    # Stop interval mode
    STOP_INTERVAL = {"name": "STOP_60"}
    # Start timer mode
    START_TIMER = {"name": "START_61"}
    # Stop timer mode
    STOP_TIMER = {"name": "STOP_61"}
    # Get bath temperature
    GET_TEMP = {"name": "IN_PV_2", "reply": {"type": float, "parser": parser.slicer, "args": [None, -2]}}
    # Get bath temperature setpoint
    GET_TEMP_SET = {"name": "IN_SP_2", "reply": {"type": float, "parser": parser.slicer, "args": [None, -2]}}
    # Set bath temperature
    SET_TEMP = {"name": "OUT_SP_2", "type": int, "check": {"min": 0, "max": 180}}
    # Get bath safety temperature
    GET_TEMP_SAFE = {"name": "IN_SP_3"}
    # Set bath safety temperature - doesn't seem to work.
    # SET_TEMP_SAFE = {"name":"OUT_SP_3", "type":int, "check":{"min":50, "max":190}}
    # Read heating medium type - doesn't seem to work
    # GET_BATH_MEDIUM = {"name":"IN_SP_74", "reply":{"type":int}}
    # Set heating bath medium type
    # SET_BATH_MEDIUM = {"name":"OUT_SP_74", "type":int, "check":{"values":HEATING_MEDIUMS}}
    # Start heating
    START_HEAT = {"name": "START_2"}
    # Stop heating
    STOP_HEAT = {"name": "STOP_2"}

    # ################### Configuration commands #############################

    # Reset rotavap & switch back to local control mode
    RESET = {"name": "RESET"}
    # Get rotavap status
    GET_STATUS = {"name": "STATUS", "reply": {"type": str}}
    # Set timer mode duration, minutes
    SET_TIMER_DURATION = {"name": "OUT_SP_60", "type": int, "check": {"min": 1, "max": 199}}
    # Set interval mode (left-right rotation) cycle time, seconds
    SET_INTERVAL_TIME = {"name": "OUT_SP_61", "type": int, "check": {"min": 1, "max": 60}}


class RV10Rotovap(AbstractRotavap):
    """
    This provides a Python class for the IKA RV10 rotavap based on the
    english section of the original operation manuals for the rotavap and the
    heating bath, 20000005206 RV10 bd_082018 and 20000017436 HB digital_092017,
    respectively.
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = RV10RotovapCommands

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

        # The rotavap activates heating/rotation upon just updating the setpoint
        # These internal variables are to track the state & make behavior more predictable.
        self._rotating = False
        self._speed_setpoint: int = 0
        self._heating = False
        self._temperature_setpoint: float = 0

    def initialize_device(self):
        """Performs reset and do a custom initialization sequence.
        """

        self.send(self.cmd.RESET)
        # This is legacy initialization from PL1
        # According to Sebastian, without it RV didn't enter remote control mode
        # TODO Check if it's actually needed
        self.start_temperature_regulation()
        self.stop_temperature_regulation()
        self.start_rotation()
        self.stop_rotation()
        self.start_task(interval=10, method=self.get_temperature)

    @in_simulation_device_returns(RV10RotovapCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks if device is connected.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        return reply == self.cmd.DEFAULT_NAME

    def is_idle(self) -> bool:
        """Checks if device is ready - no explicit method for that.
        """

        if not self.is_connected():
            return False
        return not (self._heating or self._rotating)

    def get_status(self):
        """Not yet implemented. #TODO
        """
        raise NotImplementedError

    def check_errors(self):
        """Not yet implemented. #TODO
        """
        raise NotImplementedError

    def clear_errors(self):
        """Not yet implemented. #TODO
        """
        raise NotImplementedError

    def start(self):
        """Starts evaporation.
        """

        self.start_rotation()
        self.lift_down()
        self.start_bath()

    def stop(self):
        """Stops evaporation.
        """

        self.stop_bath()
        self.lift_up()
        self.stop_rotation()

    def start_bath(self):
        """Starts heating.
        """

        self.send(self.cmd.START_HEAT)
        self._heating = True
        # This has to be done after the internal variable update
        # so that the actual device setting is updated
        self.set_temperature(self._temperature_setpoint)

    def stop_bath(self):
        """Stops heating.
        """

        self.send(self.cmd.STOP_HEAT)
        self._heating = False

    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets the desired bath temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        # If heating is not on, just update internal variable
        if not self._heating:
            # Check value against limits before updating
            self.check_value(self.cmd.SET_TEMP, temperature)
            self._temperature_setpoint = temperature
        else:
            self.send(self.cmd.SET_TEMP, temperature)
            self._temperature_setpoint = temperature

    def get_temperature(self, sensor: int = 0) -> float:
        """Gets current bath temperature.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        return self.send(self.cmd.GET_TEMP)

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Reads the current temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        return self._temperature_setpoint

    def start_rotation(self):
        """Starts rotation.
        """

        self.send(self.cmd.START_ROTATION)
        self._rotating = True
        # This has to be done after the internal variable update
        # so that the actual device setting is updated
        self.set_speed(self._speed_setpoint)

    def stop_rotation(self):
        """Stops rotation.
        """

        self.send(self.cmd.STOP_ROTATION)
        self._rotating = False

    def set_speed(self, speed: int):
        """Sets desired rotation speed.
        """

        # If rotation is not on, just update internal variable
        if not self._rotating:
            # Check value against limits before updating
            self.check_value(self.cmd.SET_SPEED, speed)
            self._speed_setpoint = speed
        else:
            self.send(self.cmd.SET_SPEED, speed)
            self._speed_setpoint = speed

    def get_speed(self) -> int:
        """Gets actual rotation speed.
        """

        return self.send(self.cmd.GET_SPEED)

    def get_speed_setpoint(self) -> int:
        """Gets current rotation speed setpoint.
        """

        return self._speed_setpoint

    def lift_up(self):
        """Move evaporation flask up.
        """

        self.send(self.cmd.LIFT_UP)

    def lift_down(self):
        """Move evaporation flask down.
        """

        self.send(self.cmd.LIFT_DOWN)
