"""PyLabware driver for Vacuubrand CVC3000 vacuum pump controller."""

import time
from collections import OrderedDict
from typing import Union, Optional, Dict, Any

import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractPressureController, in_simulation_device_returns
from ..exceptions import (PLConnectionError,
                          PLConnectionTimeoutError,
                          PLDeviceCommandError,
                          PLDeviceReplyError,
                          PLDeviceInternalError)
from ..models import LabDeviceCommands, ConnectionParameters


class CVC3000VacuumPumpCommands(LabDeviceCommands):
    """Collection of command definitions for CVC3000 vacuum controller.
    """

    # ################## Configuration constants ###########################
    DEFAULT_NAME = "CVC 3000"

    # Pump modes
    # PUMP_DOWN: continuous pumping until minimum pressure (SP_5) or timer delay (SP_6) are hit
    # VAC_CONTROL: pumping down and maintaining set pressure (SP_1) until manual stop or timer delay (SP_6) is hit
    # AUTO: Automatic pumping (with optional sensitivity) until minimum pressure (SP_5) or timer delay (SP_6) are hit
    # PROGRAM: Follow a preset vacuuming program
    OPERATION_MODES = {
        0: "VACUU_LAN",
        1: "PUMP_DOWN",
        2: "VAC_CONTROL",
        3: "AUTO",
        30: "AUTO_LOW_SENS",
        31: "AUTO_NORMAL_SENS",
        32: "AUTO_HIGH_SENS",
        4: "PROGRAM"
    }

    # Errors received for CVC 3000 configuration
    # Presented here as bit positions in the error bit field, MSB first
    ERRORS = {
        8: "Pump error!",
        7: "In-line valve error!",
        6: "Coolant valve error!",
        5: "Vent valve error!",
        4: "Overpressure error!",
        3: "Vacuum sensor error!",
        2: "External error!",
        1: "Catch pot full error!",
        0: "Last command incorrect!"
    }

    # Dictionary holding pump statuses.
    STATUSES = OrderedDict([
        ("motor_state", {0: "Pump off.", 1: "Pump on."}),
        ("inline_valve", {0: "In-line valve closed.", 1: "In-line valve open."}),
        ("coolant_valve", {0: "Coolant valve closed.", 1: "Coolant valve open."}),
        ("vent_valve", {0: "Vent valve closed.", 1: "Vent valve open."}),
        ("mode",
         {0: "VACU LAN mode.", 1: "Pumping down mode.", 2: "Vac control mode.", 3: "Auto mode.", 4: "Program mode.",
          5: "Gauge."}),
        ("control_state",
         {0: "Control off.", 1: "Reaching set point/boiling point", 2: "Set point reached/boiling point found.",
          3: "Below set point/auto switch-off."})
    ])

    # Example - pump off, vac control mode
    EXAMPLE_STATUS = "000020"

    # Languages for the CONFIGURATIONS dictionary
    LANGUAGES = {
        0: "GERMAN",
        1: "ENGLISH",
        2: "FRENCH",
        3: "ITALIAN",
        4: "SPANISH",
        5: "TURKISH",
        6: "KOREAN",
        7: "CHINESE",
        8: "PORTUGUESE",
        9: "RUSSIAN",
        10: "POLISH",  # 0xA
        11: "DUTCH",  # 0xB
        12: "JAPANESE",  # 0xC
        13: "FINNISH"  # 0xD
    }

    # Dictionary holding pump configuration.
    CONFIGURATIONS = OrderedDict([
        ("mode",
         {0: "VACU LAN mode.", 1: "Pumping down mode.", 2: "Vac control mode.", 3: "Auto mode.", 4: "Program mode.",
          5: "Gauge."}),
        ("language", LANGUAGES),
        ("unit", {0: "mbar", 1: "Torr", 2: "hPa"}),
        ("autostart", {0: "AUTOSTART OFF", 1: "AUTOSTART ON"}),
        ("acoustic_signal", {0: "ACOUSTIC SIGNAL OFF", 1: "ACOUSTIC SIGNAL ON"}),
        ("vario_pump_connected", {0: "NO VARIO PUMP", 1: "VARIO PUMP CONNECTED"}),
        ("vms_connected", {0: "NO VMS", 1: "VMS CONNECTED"}),
        ("inline_valve_connected", {0: "NO IN-LINE VALVE", 1: "IN-LINE VALVE CONNECTED"}),
        ("coolant_valve_connected", {0: "NO COOLANT VALVE", 1: "COOLANT VALVE CONNECTED"}),
        ("vent_valve_connected", {0: "NO VENT VALVE", 1: "VENT VALVE CONNECTED"}),
        ("fault_indicator_connected", {0: "NO FAULT INDICATOR", 1: "FAULT INDICATOR CONNECTED"}),
        ("level_sensor_connected", {0: "NO LEVEL SENSOR", 1: "LEVEL SENSOR CONNECTED"}),
        ("remote_module_connected", {0: "NO REMOTE MODULE", 1: "REMOTE MODULE CONNECTED"}),
        ("active_sensor", {i: i for i in range(1, 10)}),
        ("total_sensors", {i: i for i in range(1, 10)}),
        ("remote_control", {0: "REMOTE OFF", 1: "REMOTE ON"})
    ])

    # EN language, mbar, Vario pump, vent valve, active sensor 1, remote on
    EXAMPLE_CONFIG = "3100010001000111"

    # Vent valve modes
    VENT_CLOSED = 0
    VENT_OPEN = 1
    VENT_AUTO = 2

    # ################## Control Commands ###################################
    # Information requests (config, status, version)
    GET_NAME = {"name": "IN_VER", "reply": {"type": str, "parser": parser.slicer, "args": [-7]}}
    GET_VERSION = {"name": "IN_VER", "reply": {"type": float, "parser": parser.slicer, "args": [11, 15]}}
    GET_CONFIG = {"name": "IN_CFG", "reply": {"type": str}}
    GET_STATUS = {"name": "IN_STAT", "reply": {"type": str}}
    GET_ERRORS = {"name": "IN_ERR", "reply": {"type": str}}

    # Setup of Modes and configurations
    SET_MODE = {"name": "OUT_MODE", "type": int, "check": {"values": OPERATION_MODES}, "reply": {"type": int}}
    SET_CONFIG = {"name": "OUT_CFG", "type": str}  # TODO Probably develop a function for config (non needed atm)
    # CVC 300 has new command format but is factory shipped in cVC 2000 compatibility mode,
    # Thus needs switching before first use
    SET_CVC_3000 = {"name": "CVC 3000", "type": str, "reply": {"type": int}}
    # Switching back to CVC 2000 mode doesn't seem to have any practical use
    SET_CVC_2000 = {"name": "CVC 2000", "type": str, "reply": {"type": int}}

    # Get/Set the pressure
    GET_PRESSURE = {"name": "IN_PV_1", "reply": {"type": float, "parser": parser.slicer, "args": [0, 6]}}
    GET_PRESSURE_SET = {"name": "IN_SP_1", "reply": {"type": int, "parser": parser.slicer, "args": [0, 4]}}
    # This command will not enable venting after start, so might overshoot to lower pressure than needed
    # SET_PRESSURE_WITH_VENT was shown to supersede this command
    SET_PRESSURE = {"name": "OUT_SP_1", "type": int, "check": {"min": 0, "max": 1060}, "reply": {"type": int}}
    # Set the pressure with venting
    SET_PRESSURE_WITH_VENT = {"name": "OUT_SP_V", "type": int, "check": {"min": 0, "max": 1060}, "reply": {"type": int}}

    # Pump speed: Get current pump and Get/Set motor speed setpoint in %
    GET_PUMP_SPEED = {"name": "IN_PV_2", "reply": {"type": int, "parser": parser.slicer, "args": [3]}}
    GET_PUMP_SPEED_SET = {"name": "IN_SP_2", "reply": {"type": int, "parser": parser.slicer, "args": [3]}}
    SET_PUMP_SPEED = {"name": "OUT_SP_2", "type": int, "check": {"min": 0, "max": 100}, "reply": {"type": int}}

    # Venting option
    VENT_ON = {"name": "OUT_VENT 1", "reply": {"type": int}}
    VENT_OFF = {"name": "OUT_VENT 0", "reply": {"type": int}}
    # Keep venting till atmospheric pressure is reached
    VENT_ON_TO_ATM = {"name": "OUT_VENT 2", "reply": {"type": int}}

    # Start/Stop the vacuum pump
    START = {"name": "START 1", "reply": {"type": int}}
    STOP = {"name": "STOP 1", "reply": {"type": int}}

    # ################### Configuration commands ########################################
    # Communication Controls
    SET_REMOTE = {"name": "REMOTE", "type": int, "check": {"values": [0, 1]}, "reply": {"type": bool}}

    SET_ECHO = {"name": "ECHO", "type": int, "check": {"values": [0, 1]}, "reply": {"type": bool}}

    # Get uptime: Time the device has been on over its lifetime. Example response: 0062d06h<CR><LF>
    GET_UPTIME = {"name": "IN_PV_T", "reply": {"type": str}}
    # Get current process runtime. Example response: 00:03 h:m<CR><LF>
    GET_RUNTIME = {"name": "IN_PV_3", "reply": {"type": str}}

    # Set/Get start-up pressure (for two points control option)
    GET_STARTUP_PRESSURE = {"name": "IN_SP_3", "reply": {"type": int}}
    SET_STARTUP_PRESSURE = {"name": "OUT_SP_3", "type": int, "check": {"min": 0, "max": 1060}, "reply": {"type": int}}

    # Delay time for activating optional coolant valve after reaching set vacuum. Example response: 00:00 h:m<CR><LF>
    GET_DELAY_TIME = {"name": "IN_SP_4", "reply": {"type": str}}
    # Format: xx:xx (hh:mm)
    SET_DELAY_TIME = {"name": "OUT_SP_4", "type": int, "check": {"min": 1, "max": 300}, "reply": {"type": str}}

    # Switch-off pressure. This is the pressure upon reaching which the pump switches off
    # control in auto and pump down modes. IN/OUT_SP_3 doesn't apply to them.
    GET_OFF_PRESSURE = {"name": "IN_SP_5", "reply": {"type": int, "parser": parser.slicer, "args": [None, 4]}}
    SET_OFF_PRESSURE = {"name": "OUT_SP_5", "type": int, "check": {"min": 0, "max": 1060}, "reply": {"type": int}}

    # Switch-off time. This is the time limit for all modes.
    # If set above zero, pump will stop after this interval elapses after START command.
    GET_TIMER = {"name": "IN_SP_6", "reply": {"type": str, "parser": parser.slicer, "args": [None, 5]}}
    SET_TIMER = {"name": "OUT_SP_6", "type": str,
                 "reply": {"type": str, "parser": parser.slicer, "args": [None, 5]}}


class CVC3000VacuumPump(AbstractPressureController):
    """
    This provides a Python class for the Vacuubrand CVC3000 vacuum controller
    based on the the original operation manual 20901228_EN_ONLINE
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[int, str]):
        """Default constructor.
        """

        self.cmd = CVC3000VacuumPumpCommands

        # Serial connection settings - p.105 of the manual
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 19200
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["rtscts"] = True
        connection_parameters["command_delay"] = 0.3

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        # Internal variables to track status/configuration
        self._status: Dict[str, int] = {}
        self._configuration: Dict[str, Any] = {}

        super().__init__(device_name, connection_mode, connection_parameters)

    def _recv(self, cmd: Dict) -> Union[int, float, str, bool]:
        """When CVC 3000 is in echo mode, it echoes back any SET_x command
        parameter if the command has been interpreted correctly.
        If not, it doesn't reply anything, which will generate exception
        in _recv() after timeout. Thus we need to wrap it in try..catch.
        """

        try:
            return super()._recv(cmd)
        except PLConnectionTimeoutError:
            raise PLDeviceReplyError("No echo reply received from the device!") from None

    def _check_readback(self, readback: Any, value: Any) -> None:
        """Checks the CVC3000 echo reply against the parameter value sent.
        Raises PLDeviceReplyError in case readback value is wrong.
        """

        if self._simulation:
            self.logger.info("SIM:: Assert readback <%s> equals value <%s>", readback, value)
        else:
            if value != readback:
                raise PLDeviceReplyError(f"Read-back check failed! Expected <{value}>, read back <{readback}>.")

    def initialize_device(self):
        """Sets the following parameters:
        echo 'on' for all SET_x commands, to check if the command was interpreted correctly
        remote control active otherwise the device cannot accept any settings,
        set the controller to CVC 3000 which is the most comprehensive
        set the mode to vacuum control
        """

        # Echo on
        self.set_echo(True)

        # Remote on
        self.set_remote(True)

        # CVC 3000 protocol
        mode = self.send(self.cmd.SET_CVC_3000)
        self._check_readback(mode, 3)

        # Get pump configuration and current status
        self.get_configuration()
        self.get_status()

        # Set default mode - vac control
        self.set_mode(2)

        self.logger.info("Device initialized.")

    @in_simulation_device_returns(CVC3000VacuumPumpCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks if the correct device is connected by asking the name.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        return reply == self.cmd.DEFAULT_NAME

    def is_idle(self) -> bool:
        """Checks if the pump is in function at the moment.
        """

        if not self.is_connected():
            return False
        self.get_configuration()
        if self._configuration["remote_control"] != 1:
            self.logger.warning("Device remote control is switched off!")
            return False
        self.get_status()
        if self._status["control_state"] == 0:
            return True
        return False

    def set_echo(self, value: bool):
        """Toggle echo mode of the device on/off.
        When echo mode is on, pump replies with command argument for each
        command correctly recognized. If echo mode is on, but the command
        is wrong/unrecognized - the pump replies nothing.
        """

        readback = self.send(self.cmd.SET_ECHO, value)
        self._check_readback(bool(value), readback)

    def set_remote(self, value: bool):
        """Toggle the remote control of the device on/off.
        After the pump is disconnected it will remain in remote control state
        not allowing manual actions on the front panel.
        """

        readback = self.send(self.cmd.SET_REMOTE, value)
        self._check_readback(bool(value), readback)

    @in_simulation_device_returns(CVC3000VacuumPumpCommands.EXAMPLE_STATUS)
    def get_status(self, verbose: bool = False):
        """Gets device status and returns it as a list of integers
        or as a human-readable dictionary
        """

        status = self.send(self.cmd.GET_STATUS)
        if len(status) != len(self.cmd.STATUSES):
            raise PLDeviceReplyError("Received status record length doesn't match expected!")
        # Convert to list of integers
        status = list(map(int, status))
        # Map to possible statuses dictionary
        for parameter, value in zip(self.cmd.STATUSES, status):
            self._status[parameter] = value
        self.logger.info("Pump status: <%s>", self._status)
        if verbose is False:
            return status
        # Otherwise create&return human-readable status
        result = {}
        for parameter, value in zip(self.cmd.STATUSES, status):
            result[parameter] = {value: self.cmd.STATUSES[parameter][value]}
        return result

    @in_simulation_device_returns(CVC3000VacuumPumpCommands.EXAMPLE_CONFIG)
    def get_configuration(self, verbose: bool = False):
        """Gets device configuration and returns it as a list of integers
        or as a human-readable dictionary
        """

        cfg = self.send(self.cmd.GET_CONFIG)
        if len(cfg) != len(self.cmd.CONFIGURATIONS):
            raise PLDeviceReplyError("Received configuration record length doesn't match expected!")
        # Convert to list of integers
        # Hexadecimal only for language codes above 9 :/
        cfg = list(map(lambda x: int(x, base=16), cfg))
        # Map to possible statuses dictionary
        for parameter, value in zip(self.cmd.CONFIGURATIONS, cfg):
            self._configuration[parameter] = value
        self.logger.info("Pump configuration: <%s>", self._configuration)
        if verbose is False:
            return cfg
        # Otherwise create&return human-readable status
        result = {}
        for parameter, value in zip(self.cmd.CONFIGURATIONS, cfg):
            result[parameter] = {value: self.cmd.CONFIGURATIONS[parameter][value]}
        return result

    def check_errors(self):
        """Get the error string from the device and it translates it
        into a readable string. As long as the error string can contain only 1 and 0,
        unlike configuration and status strings, it can be treated as a bit field.
        """

        errors = self.send(self.cmd.GET_ERRORS)
        errors = int(errors, base=2)
        if errors != 0:
            errors_occurred = []
            for error in self.cmd.ERRORS:
                if errors & 1 << error != 0:
                    errors_occurred.append(self.cmd.ERRORS[error])
            raise PLDeviceInternalError(errors_occurred)

    def clear_errors(self):
        """Not implemented in this device, requires manual checking.
        """
        raise NotImplementedError

    def start_pressure_regulation(self):
        """Starts the pump.
        """

        if not self.is_idle():
            self.logger.warning("Pump is already running, please, stop first before starting.")
        else:
            self.send(self.cmd.START)

    def stop_pressure_regulation(self):
        """Stops the pump.
        """

        self.send(self.cmd.STOP)

    def get_mode(self) -> int:
        """Returns pump operation mode.
        """

        self.get_status()
        return self._status["mode"]

    @in_simulation_device_returns("{$args[1]}")  # Return mode in simulation
    def set_mode(self, mode):
        """Sets pump operation mode.
           When set to extended auto modes (30, 31, 32), the controller would
           always read back mode 3.
        """

        if not self.is_idle():
            self.logger.error("Changing mode not allowed while the pump is running!")
            return
        # Set mode
        readback_mode = self.send(self.cmd.SET_MODE, mode)
        # Handle readback for extended auto modes
        if mode in (30, 31, 32, "30", "31", "32"):
            mode = 3
        # Simulation decorator doesn't support value mapping, so it would return
        # extended statuses unlike the real device
        if readback_mode != int(mode) and self.simulation is False:
            raise PLDeviceReplyError(f"Failed to switch pump to mode {mode}!")
        self._status["mode"] = readback_mode

    def get_pump_speed(self) -> int:
        """Returns the current speed of the pump's motor in %.
        """

        if self._status["mode"] in (0, 3):
            raise PLDeviceCommandError("Getting/setting pump speed is not supported in VacuuLAN/Auto modes!")
        return self.send(self.cmd.GET_PUMP_SPEED)

    def get_pump_speed_setpoint(self) -> int:
        """Returns the maximum speed of the pump in %.
        """

        if self._status["mode"] in (0, 3):
            raise PLDeviceCommandError("Getting/setting pump speed is not supported in VacuuLAN/Auto modes!")
        return self.send(self.cmd.GET_PUMP_SPEED_SET)

    def set_pump_speed(self, speed: int):
        """Sets the maximum speed (1 - 100 %) the pump will reach.
        """

        if self._status["mode"] in (0, 3):
            raise PLDeviceCommandError("Getting/setting pump speed is not supported in VacuuLAN/Auto modes!")
        readback = self.send(self.cmd.SET_PUMP_SPEED, speed)
        self._check_readback(readback, int(speed))

    @in_simulation_device_returns(1013.25)
    def get_pressure(self) -> float:
        """Returns the current pressure. In simulation returns atmospheric
        pressure.
        """

        return self.send(self.cmd.GET_PRESSURE)

    def set_pressure(self, pressure: float):
        """Sets the pressure to be reached, in millibar.
        Takes pressure as a float to comply w/ AbstractPressureController,
        but the device only understands mbar (int).
        """

        # SET_PRESSURE_WITH_VENT allows venting with internal CVC 3000 vent valve
        # in case the pump overshoots and pressure goes too much down.
        # It also handles the situations when you the pump is holding vacuum
        # at the setpoint and you want to go up in the pressure (lower vacuum)
        readback = self.send(self.cmd.SET_PRESSURE_WITH_VENT, pressure)
        self._check_readback(readback, int(pressure))

    def get_pressure_setpoint(self) -> int:
        """Returns the pressure setpoint, in millibar.
        """

        return self.send(self.cmd.GET_PRESSURE_SET)

    def set_end_pressure(self, pressure: int):
        """Sets the the end pressure for auto mode and pump down mode.
        After this pressure is reached or the timeout has elapsed
        (whichever happens first), the pump switches off.
        """

        # A bug in CVC 3000 firmware doesn't allow to set the pressure above
        # 300 mbar in auto mode - see #25
        # In that case pump records command error and the setpoint value remains
        # unchanged. If SP5 setpoint was set above 300 mbar in any other mode,
        # it gets set to 300 upon switching to auto mode.
        if self._status["mode"] == 3 and pressure > 300:
            self.logger.error("Due to FW error switch-off pressure in AUTO mode cannot be set above 300 mbar."
                              "Falling back to 300.")
            pressure = 300
        readback = self.send(self.cmd.SET_OFF_PRESSURE, pressure)
        self._check_readback(readback, int(pressure))

    def get_end_pressure_setpoint(self) -> int:
        """Returns the end pressure setpoint.
        """

        return self.send(self.cmd.GET_OFF_PRESSURE)

    def set_end_timeout(self, timeout: int):
        """Sets end time for pump down and auto mode. After this time has elapsed
        or switch-off pressure is reached (whichever happens first),
        the pump switches off.

        Args:
            timeout (int): Vacuum pump timeout time in seconds.

        Exceptions:
            Raises PLDeviceCommandError if the timeout value is not within the range from 1 s
                to 86400 s.
        """

        # FIXME has to be removed with the new value checking/formatting framework
        if timeout < 1 or timeout > 86400:
            raise PLDeviceCommandError(f"Received invalid pump timeout value of {timeout} s. Pump timeout value must be withing 1 s to 86400 s (1 day).")

        # Convert time in seconds to hh:mm string required by the pump
        timeout = time.strftime('%H:%M', time.gmtime(int(timeout)))
        readback = self.send(self.cmd.SET_TIMER, timeout)
        self._check_readback(readback, timeout)

    @in_simulation_device_returns("00:30")
    def get_end_timeout(self):
        """Gets end time value in seconds.
        """

        reply = self.send(self.cmd.GET_TIMER)
        timeout = int(reply.split(":")[0]) * 60 + int(reply.split(":")[1])
        return timeout

    def is_vent_open(self) -> bool:
        """Checks if the vent is open.
        """

        self.get_status()
        if self._status["vent_valve"] == 1:
            return True
        return False

    def vent_on(self):
        """Opens the air admittance valve.
        """

        readback = self.send(self.cmd.VENT_ON)
        self._check_readback(readback, self.cmd.VENT_OPEN)

    def vent_off(self):
        """Closes the air admittance valve.
        """

        readback = self.send(self.cmd.VENT_OFF)
        self._check_readback(readback, self.cmd.VENT_CLOSED)

    def vent_auto(self):
        """Automatically vents the pump to the atmospheric pressure.
        """

        readback = self.send(self.cmd.VENT_ON_TO_ATM)
        self._check_readback(readback, self.cmd.VENT_AUTO)

    @property
    def unit(self):
        """Get pressure unit that the device is currently operating with.

        Returns:
            str: Pressure unit that the device is currently operating with. One
            of 'mbar', 'Torr' or 'hPa'. If :py:attr`initialize_device` has not
            been called then return ``None``.
        """
        return self.cmd.CONFIGURATIONS['unit'][self._configuration['unit']]
