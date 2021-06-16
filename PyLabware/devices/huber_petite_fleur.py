"""PyLabware driver for Huber Petite Fleur chiller."""

from time import sleep
from typing import Tuple, Optional, Union
import serial

# Core import
import PyLabware.parsers as parser
from PyLabware.controllers import (
    AbstractTemperatureController, in_simulation_device_returns)
from PyLabware.exceptions import (PLConnectionError,
                                      PLDeviceCommandError,
                                      PLDeviceReplyError)
from PyLabware.models import LabDeviceCommands, ConnectionParameters


class PetiteFleurChillerCommands(LabDeviceCommands):
    """Collection of command definitions for Huber PetiteFleur chiller."""

    # ################### Configuration constants #############################
    DEFAULT_NAME = "Huber device"

    # Default prefix for every command
    COMMAND_PREFIX = "{M"

    STATUSES = [
        "Temperature control operating mode: ",
        "Circulation operating mode: ",
        "Refrigerator compressor mode: ",
        "Temperature control mode: ",
        "Circulating Pump: ",
        "Cooling power available: ",
        "KeyLock: ",
        "PID parameter set: ",
        "Error detected: ",
        "Warning message detected: ",
        "Mode for setting the internal temperature(0X08): ",
        "Mode for setting the external temperature(0X09): ",
        "DV E-grade: ",
        "Power failure: ",
        "Freeze protection: "
    ]

    # Control Commands
    # The string is actually an hex from -15111 to 50000 (in cent of °C)
    SET_TEMP_SP = {"name": "{M00", "type": str, "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    # The string is actually an hex from -15111 to 50000 (in cent of °C)
    GET_TEMP_SP = {"name": "{M00****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    # The string is actually an hex from -15111 to 50000 (in cent of °C)
    GET_TEMP_BATH = {"name": "{M01****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_PUMP_PRESSURE = {"name": "{M03****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_ERRORS = {"name": "{M05****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_WARNINGS = {"name": "{M06****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_PROCESS_TEMP = {"name": "{M07****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_STATUS = {"name": "{M0A****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    STOP_TEMP_CONTROL = {"name": "{M140000", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    START_TEMP_CONTROL = {"name": "{M140001", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    # Possible values - 0, 1, 2. It seems without any effect
    SET_PUMP_MODE = {"name": "{M15", "type": str, "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    STOP_CIRCULATOR = {"name": "{M160000", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    START_CIRCULATOR = {"name": "{M160001", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}

    # Temperature Ramping Commands (probably not implemented in PetiteFleur firmware)
    START_TEMPERATURE_CTRL = {"name": "{M58", "type": str,
                              "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    SET_RAMP_DURATION = {"name": "{M59", "type": str, "reply": {"type": str, "parser": parser.slicer,
                                                                "args": [4, 8]}}  # from 0000 -> FFFF (65535) seconds
    START_RAMP = {"name": "{M5A", "type": str, "reply": {"type": str, "parser": parser.slicer, "args": [4,
                                                                                                        8]}}  # associated with the target temperature in 16 bit hex
    GET_RAMP_TEMP = {"name": "{M5A****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    GET_RAMP_TIME = {"name": "{M59****", "reply": {"type": str, "parser": parser.slicer, "args": [4, 8]}}
    # Extras
    KEY_LOCK = {"name": "{M17", "type": str, "reply": {"type": str}}  # Locks the manual interface in the system with 1


class PetiteFleurChiller(AbstractTemperatureController):
    """
    This provides a Python class for the Huber Petite Fleur
    chiller based on the the original operation manual
    V1.8.0en/06.10.17
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        self.cmd = PetiteFleurChillerCommands
        # serial settings
        # all settings are at default
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["command_delay"] = 1.0

        super().__init__(device_name, connection_mode, connection_parameters)
        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = ""

    def initialize_device(self):
        """ This chiller doesn't need/have any initialization.
        """

    def is_connected(self) -> bool:
        """Tries to get chiller status & compares it to the template value.
        """

        try:
            status = self.get_status()
        except PLConnectionError:
            return False
        return len(status) == len(self.cmd.STATUSES)

    def is_idle(self) -> bool:
        """Checks whether the chiller is running.
        #TODO Probably rather has to be done by checking device status.
        """

        if not self.is_connected():
            return False
        p = self.get_pump_pressure()
        return p < 5

    def get_errors(self):
        """ Not implemented yet. #TODO
        """

        raise NotImplementedError

    def clear_errors(self):
        """ Not implemented yet. #TODO
        """

        raise NotImplementedError

    def check_errors(self):
        """ Not implemented yet. #TODO
        """

        raise NotImplementedError

    def temp_transform(self, temp) -> float:
        """Returns the temperature transformed into appropriate number:
        16 bit signed integer.
        """

        res = temp & 0b0111111111111111
        if res == temp:
            return float(res) / 100
        return float(res - 0X8000) / 100

    def start_temperature_regulation(self):
        """Starts the chiller.
        """

        # start circulation
        t = self.send(self.cmd.START_TEMP_CONTROL)
        # The 10 + 5 s delay is needed because during the start of the machine no other command
        # should be allowed, otherwise silent crash of the system without answer occurs
        sleep(10)
        # start temperature control
        p = self.send(self.cmd.START_CIRCULATOR)
        sleep(5)
        return bool(int(p and t))

    @in_simulation_device_returns('0')
    def stop_temperature_regulation(self):
        """Stops the chiller.
        """

        # stop temperature control
        p = self.send(self.cmd.STOP_CIRCULATOR)
        # stop circulation
        t = self.send(self.cmd.STOP_TEMP_CONTROL)
        return int(p and t) == 0

    @in_simulation_device_returns("{$args[1]}")
    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets the target temperature of the chiller.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has one common setpoint temperature shared by the external and internal probe.
                          Thus, the sensor variable has no effect here.
        """

        # setting the setpoint
        if -151 <= temperature <= 327:
            temperature = int(temperature * 100)
            temperature = temperature & 0xFFFF
            readback_temp = self.send(self.cmd.SET_TEMP_SP, "{:04X}".format(temperature))
            if readback_temp is None:
                raise PLDeviceReplyError(f"Error setting temperature. Requested setpoint <{temperature}>, read back setpoint <{readback_temp}>")
        else:
            raise PLDeviceCommandError("Temperature value OUT OF RANGE! \n")

    def get_temperature(self, sensor: int = 0) -> float:
        """Reads the current temperature of the bath

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has one common setpoint temperature shared by the external and internal probe.
                          Thus, the sensor variable has no effect here.
        """

        answer = self.send(self.cmd.GET_TEMP_BATH)
        return self.temp_transform(int(answer, base=16))

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Reads the current temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has one common setpoint temperature shared by the external and internal probe.
                          Thus, the sensor variable has no effect here.
        """

        answer = self.send(self.cmd.GET_TEMP_SP)
        return self.temp_transform(int(answer, base=16))

    # It seems it doesn't work although the manual says it should
    def ramp_temperature(self, end_temperature: float, time: int):
        """
        Sets the duration for a temperature ramp in seconds.
        Range is -32767...32767s where negative values cancel the
        ramp. Maximum ramp is a tad over 9 hours.
        """

        # setting the setpoint
        if -32767 <= time <= 32767:
            ramp_duration_hex = "{:04X}".format(time & 0xFFFF)  # convert to two's complement hex string
            reply = self.send(self.cmd.SET_RAMP_DURATION, ramp_duration_hex)
            if (reply is not None) and (-151 <= end_temperature <= 327):
                end_temperature = int(end_temperature * 100)  # convert to appropriate decimal format
                end_temperature_hex = "{:04X}".format(end_temperature & 0xFFFF)  # convert to two's complement hex string
                self.send(self.cmd.START_RAMP, end_temperature_hex)
            else:
                raise PLDeviceCommandError('The requested setpoint is out of range!')
        else:
            raise PLDeviceCommandError('The requested duration is out of range!')

    def get_ramp_details(self) -> Tuple[int, float]:
        """Get remaining time and target temperature for the ramp.
        """

        rem_time = self.send(self.cmd.GET_RAMP_TIME)
        rem_time = int(rem_time, base=16)
        targ_temp = self.send(self.cmd.GET_RAMP_TEMP)
        targ_temp = int(targ_temp, base=16)
        return rem_time, self.temp_transform(targ_temp)

    def start_temp_ctrl(self, program: str) -> int:
        """Starts the temperature control program input from 0001 -> 0010
        """

        choice = self.send(self.cmd.START_TEMPERATURE_CTRL, program)
        choice = int(choice, base=16)
        return choice

    def get_status(self) -> str:
        """Returns the status of the chiller.
        """

        s = self.send(self.cmd.GET_STATUS)
        return '{:015b}'.format(int(s, 16) & 0b111111111111111)

    def interpret_status(self, status_string: str) -> str:
        """Interprets the status string to return human-readable status
        """

        ret = ""
        ans = {'0': 'INACTIVE', '1': 'ACTIVE'}
        p7 = {'0': 'Expert Mode', '1': 'Automatic Mode'}
        p13 = {'1': 'No Failure', '0': 'System restarted'}
        p5_8_9 = {'0': 'NO', '1': 'YES'}
        count = 0
        for i in status_string:
            if count == 7:
                ret += self.cmd.STATUSES[count] + p7[i] + "\n"
            elif count in (5, 8, 9):
                ret += self.cmd.STATUSES[count] + p5_8_9[i] + "\n"
            elif count == 13:
                ret += self.cmd.STATUSES[count] + p13[i] + "\n"
            else:
                ret += self.cmd.STATUSES[count] + ans[i] + "\n"
            count += 1
        return ret

    def get_pump_pressure(self) -> int:
        """Returns the pump pressure (can be used as measure of the pump activity).
        """

        reply = self.send(self.cmd.GET_PUMP_PRESSURE)
        return int(reply, base=16) - 1000

    def set_circulator_control(self, pump_mode: int):
        """Sets the compressor control mode.
        """

        self.send(self.cmd.SET_PUMP_MODE, "{:04X}".format(pump_mode & 0XFFFF))
