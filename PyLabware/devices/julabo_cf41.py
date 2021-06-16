"""PyLabware driver for Julabo CF41 chiller."""

import threading
from time import sleep
from typing import Optional, Union

import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractTemperatureController, in_simulation_device_returns
from ..exceptions import (PLConnectionError,
                          PLDeviceCommandError,
                          PLDeviceInternalError,
                          PLDeviceReplyError)
from ..models import LabDeviceCommands, ConnectionParameters


class CF41ChillerCommands(LabDeviceCommands):
    """Collection of command definitions for CF41 chiller.
    """

    # ################### Configuration constants #############################
    DEFAULT_NAME = "JULABO CRYOCOMPACT CF41"

    # Selected setpoint to use
    SETPOINT_MODES = {0: "SP1", 1: "SP2", 2: "SP3"}

    # Self-tuning modes
    SELFTUNE_MODES = {0: "SELFTUNE_OFF", 1: "SELFTUNE_ONCE", 2: "SELFTUNE_ALWAYS"}

    # External programmer input modes. 0 - voltage 0..10V; 1 - current 0..20mA
    EXTPROG_MODES = {0: "EXT_VOLTAGE", 1: "EXT_CURRENT"}

    # Temperature regulation mode. 0 - internal; 1 - external Pt100
    REGULATION_MODES = {0: "INTERNAL", 1: "EXTERNAL"}

    # Control dynamics modes
    CONTROL_DYNAMCIS_MODES = {0: "APERIODIC", 1: "STANDARD"}

    # Pump speed modes
    PUMP_SPEED_MODES = [1, 2, 3, 4]

    STATUSES = {
        "00": "STOPPED",
        "02": "STOPPED",
        "01": "STARTED",
        "03": "STARTED"
    }

    # Non critical errors. User has to be notified, but device can keep operating.
    WARNINGS = {
        "-10": "Entered value too small!",
        "-11": "Entered value too large!",
        "-15": "External control selected, but Pt100 sensor not connected.",
        "-20": "Check air cooled condenser.",
        "-21": "Compressor stage 1 does not work.",
        "-26": "Stand-by plug is missing.",
        "-33": "Safety temperature sensor short-circuited or open!",
        "-38": "External Pt100 sensor error!",
        "-40": "Coolant level low"
    }

    # Critical errors. Device operation is not possible until the error is cleared.
    ERRORS = {
        "-01": "Coolant level critically low!",
        "-03": "Coolant temperature too high!",
        "-04": "Coolant temperature too low!",
        "-05": "Working temperature sensor short-circuited or open!",
        "-06": "Temperature difference between working and safety temperature is above 35°C!",
        "-07": "Internal I2C bus error!",
        "-08": "Invalid command!",
        "-09": "Invalid command in current operating mode!",
        "-12": "Internal ADC error!",
        "-13": "Set temperature value exceeds safety limits!",
        "-14": "Excess temperature protection alarm",

    }

    # ################### Control commands ###################################

    # Get software version
    GET_VERSION = {"name": "VERSION", "reply": {"type": str, "parser": parser.slicer, "args": [-3]}}
    # Get device name
    GET_NAME = {"name": "VERSION", "reply": {"type": str, "parser": parser.slicer, "args": [0, 23]}}
    # Get status/error message
    GET_STATUS = {"name": "STATUS", "reply": {"type": str, "parser": parser.slicer, "args": [0, 2]}}

    # Get/set working temperature - setpoint 1
    GET_TEMP_SP1 = {"name": "IN_SP_00", "reply": {"type": float}}
    # Most of the chillers have H5 cooling fluid which has recommended temperature -40..110 ºC
    SET_TEMP_SP1 = {"name": "OUT_SP_00", "type": float, "check": {"min": -40, "max": 110}}

    # Get/set working temperature - setpoint 2
    GET_TEMP_SP2 = {"name": "IN_SP_01", "reply": {"type": float}}
    SET_TEMP_SP2 = {"name": "OUT_SP_01", "type": float, "check": {"min": -40, "max": 110}}

    # Get/set working temperature - setpoint 3
    GET_TEMP_SP3 = {"name": "IN_SP_02", "reply": {"type": float}}
    SET_TEMP_SP3 = {"name": "OUT_SP_02", "type": float, "check": {"min": -40, "max": 110}}

    # Get/set pump speed mode
    GET_PUMP_SPEED = {"name": "IN_SP_07", "reply": {"type": int}}
    SET_PUMP_SPEED = {"name": "OUT_SP_07", "type": int, "check": {"values": PUMP_SPEED_MODES}}

    # Get/set maximum cooling power
    GET_MAX_COOL_PWR = {"name": "IN_HIL_00", "reply": {"type": int}}
    SET_MAX_COOL_PWR = {"name": "OUT_HIL_00", "type": int, "check": {"min": -100, "max": 0}}
    # Get/set maximum heating power
    GET_MAX_HEAT_PWR = {"name": "IN_HIL_01", "reply": {"type": int}}
    SET_MAX_HEAT_PWR = {"name": "OUT_HIL_01", "type": int, "check": {"min": 10, "max": 100}}

    # Start the chiller
    START_CHILLER = {"name": "OUT_MODE_05 1"}
    # Stop the chiller
    STOP_CHILLER = {"name": "OUT_MODE_05 0"}
    # Get chiller state
    GET_CHILLER_STATE = {"name": "IN_MODE_05", "reply": {"type": int}}

    # Get actual bath temperature
    GET_TEMP_INT = {"name": "IN_PV_00", "reply": {"type": float}}
    # Get heating power, %
    GET_HEAT_PWR = {"name": "IN_PV_01", "reply": {"type": float}}
    # Get temperature from external Pt100 sensor
    GET_TEMP_EXT = {"name": "IN_PV_02", "reply": {"type": float}}
    # Get safety sensor temperature
    GET_TEMP_SAFE = {"name": "IN_PV_03", "reply": {"type": float}}
    # Get safety temperature setpoint
    GET_TEMP_SAFE_SET = {"name": "IN_PV_04", "reply": {"type": float}}

    # Get/set high temperature warning limit
    GET_TEMP_LIM_HI = {"name": "IN_SP_03", "reply": {"type": float}}
    # Room temperature to maximum temp the chiller can reach
    SET_TEMP_LIM_HI = {"name": "OUT_SP_03", "type": float, "check": {"min": 20, "max": 190}}

    # Get/set low temperature warning limit
    GET_TEMP_LIM_LO = {"name": "IN_SP_04", "reply": {"type": float}}
    # Room temperature to minimum temperature the chiller can reach
    SET_TEMP_LIM_LO = {"name": "OUT_SP_04", "type": float, "check": {"min": -40, "max": 19}}

    # Get value from external flowrate sensor
    GET_EXT_FLOWRATE = {"name": "IN_SP_08", "reply": {"type": float}}
    # Get temperature difference between working and safety sensor
    GET_TEMP_DELTA = {"name": "IN_PAR_00", "reply": {"type": float}}
    # Get time constant for external bath
    GET_BATH_TE_EXT = {"name": "IN_PAR_01", "reply": {"type": float}}
    # Get internal slope
    GET_SI = {"name": "IN_PAR_02", "reply": {"type": float}}
    # Time constant for internal bath
    GET_BATH_TE_INT = {"name": "IN_PAR_03", "reply": {"type": float}}
    # Get bath temperature band limit
    GET_BATH_BAND_LIMIT = {"name": "IN_PAR_04", "reply": {"type": float}}

    # Get self-tuning mode. 0 - off; 1 - once; 2 - always
    GET_SELFTUNE_MODE = {"name": "IN_MODE_02", "reply": {"type": int}}

    # Get type of ext programmer input.
    GET_EXTPROG_MODE = {"name": "IN_MODE_03", "reply": {"type": int}}

    # Get/set temperature control mode. 0 - internal; 1 - external.
    GET_TEMP_REG_MODE = {"name": "IN_MODE_04", "reply": {"type": int}}
    # Set temperature regulation mode
    SET_TEMP_REG_MODE = {"name": "OUT_MODE_04", "type": int, "check": {"values": REGULATION_MODES}}

    # Get control dynamics mode. 0 - aperiodic; 1 - standard
    GET_DYN_MODE = {"name": "IN_MODE_08", "reply": {"type": int}}

    # ################### Configuration commands #############################

    # Get/set temperature setpoint to use (SP1..SP3)
    SET_TEMP_SP = {"name": "OUT_MODE_01", "type": int, "check": {"values": SETPOINT_MODES}}
    GET_TEMP_SP = {"name": "IN_MODE_01", "reply": {"type": int}}
    # Set self-tune mode
    SET_SELFTUNE_MODE = {"name": "OUT_MODE_02", "type": int, "check": {"values": SELFTUNE_MODES}}
    # Set external programmer mode
    SET_EXTPROG_MODE = {"name": "OUT_MODE_03", "type": int, "check": {"values": EXTPROG_MODES}}
    # Set manipulated variable for the heater via serial interface
    SET_HEATER_VALUE = {"name": "OUT_SP_06", "type": int, "check": {"min": -100, "max": 100}}
    # Set cospeed for external control
    SET_COSPEED_EXT = {"name": "OUT_PAR_04", "type": float, "check": {"min": 0, "max": 5}}
    # Set control dynamics mode
    SET_CONTROL_MODE = {"name": "OUT_MODE_08", "type": int, "check": {"values": CONTROL_DYNAMCIS_MODES}}
    # Get setpoint temperature of external programmer
    GET_TEMP_EXTPROG = {"name": "IN_SP_05", "reply": {"type": float}}
    # Get temperature indication: 0-°C, 1-°F
    GET_TEMP_UNITS = {"name": "IN_SP_06", "reply": {"type": float}}
    # Get pk/ph0 factor (ratio between max cooling and max heating capacity)
    GET_PKPH0 = {"name": "IN_PAR_05", "reply": {"type": float}}

    # Get/set Xp control parameter of the internal controller
    GET_XP_INT = {"name": "IN_PAR_06", "reply": {"type": float}}
    SET_XP_INT = {"name": "OUT_PAR_06", "type": float, "check": {"min": 0.1, "max": 99.9}}

    # Get/set Tn control parameter of the internal controller
    GET_TN_INT = {"name": "IN_PAR_07", "reply": {"type": int}}
    SET_TN_INT = {"name": "OUT_PAR_07", "type": int, "check": {"min": 3, "max": 9999}}

    # Get/set Tv control parameter of the internal controller
    GET_TV_INT = {"name": "IN_PAR_08", "reply": {"type": int}}
    SET_TV_INT = {"name": "OUT_PAR_08", "type": int, "check": {"min": 0, "max": 999}}

    # Get/set Xp control parameter of the cascaded controller
    GET_XP_CAS = {"name": "IN_PAR_09", "reply": {"type": float}}
    SET_XP_CAS = {"name": "OUT_PAR_09", "type": float, "check": {"min": 0.1, "max": 99.9}}

    # Get/set proportional coefficient of the cascaded controller
    GET_PROP_CAS = {"name": "IN_PAR_10", "reply": {"type": float}}
    SET_PROP_CAS = {"name": "OUT_PAR_10", "type": float, "check": {"min": 1, "max": 99.9}}

    # Get/set Tn control parameter of the cascaded controller
    GET_TN_CAS = {"name": "IN_PAR_11", "reply": {"type": int}}
    SET_TN_CAS = {"name": "OUT_PAR_11", "type": int, "check": {"min": 3, "max": 9999}}

    # Get/set Tn control parameter of the cascaded controller
    GET_TV_CAS = {"name": "IN_PAR_12", "reply": {"type": int}}
    SET_TV_CAS = {"name": "OUT_PAR_12", "type": int, "check": {"min": 0, "max": 999}}

    # Get/set adjusted maximum internal temperature for the cascaded controller
    GET_TEMP_CAS_MAX = {"name": "IN_PAR_13", "reply": {"type": float}}
    SET_TEMP_CAS_MAX = {"name": "OUT_PAR_13", "type": float}

    # Get/set adjusted minimum internal temperature for the cascaded controller
    GET_TEMP_CAS_MIN = {"name": "IN_PAR_14", "reply": {"type": float}}
    SET_TEMP_CAS_MIN = {"name": "OUT_PAR_14", "type": float}

    # Get/set upper band limit
    GET_BAND_LIM_HI = {"name": "IN_PAR_15", "reply": {"type": int}}
    SET_BAND_LIM_HI = {"name": "OUT_PAR_15", "type": int, "check": {"min": 0, "max": 200}}

    # Get/set lower band limit
    GET_BAND_LIM_LO = {"name": "IN_PAR_16", "reply": {"type": int}}
    SET_BAND_LIM_LO = {"name": "OUT_PAR_16", "type": int, "check": {"min": 0, "max": 200}}


class CF41Chiller(AbstractTemperatureController):
    """
    This provides a Python class for the Julabo CF41 chiller based on the
    the original operation manual 1.951.4871-V3 11/15 26.11.15
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor
        """

        self.cmd = CF41ChillerCommands

        # Serial connection settings - p.71 of the manual
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.SEVENBITS
        connection_parameters["parity"] = serial.PARITY_EVEN
        connection_parameters["rtscts"] = True
        connection_parameters["command_delay"] = 0.3

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        super().__init__(device_name, connection_mode, connection_parameters)

    def initialize_device(self):
        """This chiller doesn't have initialization method.
        """

    @in_simulation_device_returns("00")  # Stopped, no error
    def get_status(self) -> str:
        """Gets chiller status.
        """

        return self.send(self.cmd.GET_STATUS)

    def check_errors(self):
        """Checks device for errors.
        """
        status = self.get_status()
        # All OK
        if status in self.cmd.STATUSES:
            self.logger.debug("get_status()::status: <%s>", self.cmd.STATUSES[status])
            return
        # Warning
        if status in self.cmd.WARNINGS:
            self.logger.warning("Warning! %s", self.cmd.WARNINGS[status])
            return
        # Critical error
        if status in self.cmd.ERRORS:
            self.logger.error("Critical error: %s", self.cmd.ERRORS[status])
            raise PLDeviceInternalError(self.cmd.ERRORS[status])
        errmsg = f"Unknown status {status} received from device!"
        self.logger.error(errmsg)
        raise PLDeviceReplyError(errmsg)

    def clear_errors(self):
        """Not yet implemented. #TODO
        """
        raise NotImplementedError

    @in_simulation_device_returns(CF41ChillerCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks if teh chiller is connected.
        """

        try:
            name = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        return name == self.cmd.DEFAULT_NAME

    @in_simulation_device_returns(0)
    def is_idle(self) -> bool:
        """
        Returns true if the chiller is off: pump and temperature control
        """

        if not self.is_connected():
            return False
        status = self.send(self.cmd.GET_CHILLER_STATE)
        return status == 0

    def start_temperature_regulation(self):
        """Starts the chiller
        """

        self.send(self.cmd.START_CHILLER)

    def stop_temperature_regulation(self):
        """Stops the chiller
        """

        self.send(self.cmd.STOP_CHILLER)

    def get_regulation_mode(self) -> int:
        """Gets current temperature regulation mdoe.
        """

        return self.send(self.cmd.GET_TEMP_REG_MODE)

    def set_regulation_mode(self, mode: int):
        """Sets chiller temperature regulation mode.
        """

        # Check if we got valid mode
        if mode not in self.cmd.REGULATION_MODES:
            raise PLDeviceCommandError("Invalid regulation mode provided!")
        self.send(self.cmd.SET_TEMP_REG_MODE, mode)

    @in_simulation_device_returns("{$args[1]}")
    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets the target temperature of the chiller.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          The Julabo CF41 chiller has one common setpoint temperature
                          shared by the external and internal probe. Thus, the sensor variable has no effect here.
        """

        # Check which SP is currently active
        setpoint_active = self.get_active_setpoint()

        # Choose the setpoint
        if setpoint_active == 0:
            self.send(self.cmd.SET_TEMP_SP1, temperature)
        elif setpoint_active == 1:
            self.send(self.cmd.SET_TEMP_SP2, temperature)
        elif setpoint_active == 2:
            self.send(self.cmd.SET_TEMP_SP3, temperature)
        else:
            raise PLDeviceCommandError(f"Invalid active SP <{setpoint_active}> received from the device!")

    @in_simulation_device_returns(0)
    def get_active_setpoint(self) -> int:
        """ Gets currently active temperature setpoint.
        """

        return self.send(self.cmd.GET_TEMP_SP)

    def get_temperature(self, sensor: int = 0) -> float:
        """Retrieves the current temperature of the chiller.
        This can be the internal or external temperature, depending
        in what mode the chiller is currently operating.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
        """

        # First, get regulation mde from the chiller
        mode = self.get_regulation_mode()
        if mode is None:
            # The chiller returned an invalid mode.
            raise PLDeviceReplyError(f"Received invalid mode '{mode}' from the chiller "
                                     f"'{self.device_name}'. Valid modes are '0' (internal "
                                     "regulation mode) and '1' (external regulation mode).")
        # Invalid sensor requested
        if sensor not in self.cmd.REGULATION_MODES.keys():
            raise PLDeviceCommandError(f"Invalid sensor number {sensor} provided!"
                                       f"Allowed values are {self.cmd.REGULATION_MODES}")
        # Check if the sensor requested matches the regulation modes (0 - internal; 1 - external)
        # FIXME
        # If external probe is not connected, chiller returns "---.--"
        # which would throw an exception from parse_reply() when requesting external sensor reading
        if sensor != mode:
            self.logger.warning("Chiller currently operates in {mode} regulation mode, "
                                "but the reading from sensor {sensor} ({self.cmd.REGULATION_MODES[sensor]}) was requested!")
        # Internal sensor temperature
        if sensor == 0:
            return self.send(self.cmd.GET_TEMP_INT)
        # External sensor temperature
        if sensor == 1:
            return self.send(self.cmd.GET_TEMP_EXT)

    @in_simulation_device_returns(0)
    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Reads the current temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device uses a shared setpoint for all temperature probes.
                          Hence, this argument has no effect here.
        """

        # Check which SP is currently active
        setpoint_active = self.get_active_setpoint()

        if setpoint_active == 0:
            return self.send(self.cmd.GET_TEMP_SP1)
        if setpoint_active == 1:
            return self.send(self.cmd.GET_TEMP_SP2)
        if setpoint_active == 2:
            return self.send(self.cmd.GET_TEMP_SP3)
        raise PLDeviceReplyError(f"Invalid active SP <{setpoint_active}> received from the device!")

    # FIXME this should be refactored with new background tasks functionality
    def ramp_temperature(self, end_temperature: float, time: float):
        """Ramps chiller temperature from the current temperature
        to the end_temperature over time.
        """

        if self.is_idle():
            self.logger.warning("Chiller is not running! Please start the chiller before ramping the temperature.")
            return
        # Get starting temperature
        start_temperature = self.get_temperature()
        # Temperature step, degrees per minute. Can be either positive or negative.
        ramp_step = (end_temperature - start_temperature) / time
        # Check if the value is sane
        # Upon manual testing, chiller was able to reliably ramp temperature to 40 °C over 900 minutes.
        # This gives approximately 0.044 °C/min step
        # 3 decimal places would be enough to minimize the error
        ramp_step = round(ramp_step, 3)
        if ramp_step > 5.0 or ramp_step < -2.0:
            self.logger.error("Ramp step <%s> °C/min is too steep to ramp reliably!", ramp_step)
        elif abs(ramp_step) < 0.05:
            self.logger.error("Ramp step <%s> °C/min is very low!", ramp_step)
        self.logger.debug("ramp_temperature()::calculated ramp from <%s> to <%s> over <%s> minutes; step - <%s> degrees/min",
                          start_temperature, end_temperature, time, ramp_step)

        ramp_thread = threading.Thread(target=self._ramp_runner, args=(start_temperature, ramp_step, end_temperature), daemon=True)
        ramp_thread.start()
        return ramp_step

    def _ramp_runner(self, start: float, step: float, end: float):
        """Worker function that actually does the ramp.
        """

        current_temperature = start + step
        self.logger.info("Ramp start.")
        while (step > 0 and current_temperature <= end) or (step < 0 and current_temperature >= end):
            self.logger.info("Ramping from %s to %s, current step <%s>, %s minutes left",
                             start, end, current_temperature, abs(round(end - current_temperature)))
            self.set_temperature(current_temperature)
            # Calculate next value
            current_temperature = round(current_temperature + step, 2)
            sleep(60)
        self.logger.info("Ramp end.")
        # Set temperature to final value
        self.set_temperature(end)

    @in_simulation_device_returns(0)
    def get_cooling_power(self) -> int:
        """Returns the value of the chiller cooling power in %
        """

        return abs(self.send(self.cmd.GET_MAX_COOL_PWR))

    def set_cooling_power(self, cooling_power: int):
        """Sets the value of the chiller cooling power in %
        """

        # According to manual, "Enter the value with a preceding negative sign!"
        cooling_power = -abs(cooling_power)
        self.send(self.cmd.SET_MAX_COOL_PWR, cooling_power)

    def get_heating_power(self) -> float:
        """Returns the current heating power in %.
        """

        return self.send(self.cmd.GET_HEAT_PWR)

    def get_heating_power_setpoint(self) -> int:
        """Returns the value of the heating power setpoint in %
        """

        return self.send(self.cmd.GET_MAX_HEAT_PWR)

    def set_heating_power(self, heating_power: int = 100):
        """Sets the heating power of the chiller, in percent [10-100%].
        """

        heating_power = abs(heating_power)
        self.send(self.cmd.SET_MAX_HEAT_PWR, heating_power)

    def set_recirculation_pump_speed(self, speed: int):
        """Sets the recirculation pump speed (4 different speeds allowed).
        """
        self.send(self.cmd.SET_PUMP_SPEED, speed)

    def get_recirculation_pump_speed(self) -> int:
        """Returns the recirculation pump speed:
        1 (low flow rate) --> 4 (high flow rate)
        """

        return self.send(self.cmd.GET_PUMP_SPEED)
