"""PyLabware driver for Heidolph HeiTorque 100 Control overhead stirrer."""

import re

from typing import Any, Optional, Dict, Union
import serial


# Core imports
from .. import parsers as parser
from ..controllers import AbstractStirringController, in_simulation_device_returns
from ..exceptions import (PLConnectionError,
                          PLDeviceInternalError,
                          PLDeviceReplyError)
from ..models import LabDeviceCommands, ConnectionParameters


class HeiTorque100PrecisionStirrerCommands(LabDeviceCommands):
    """Collection of command definitions for HeiTorque 100 Control overhead stirrer.
    """

    # ################### Configuration constants #############################
    NO_ERROR = "No Error!"
    MOTOR_ERROR = "Motor Error!"
    OVERHEAT_ERROR = "Motor Temperature!"
    OVERLOAD_ERROR = "Overload!"
    MANUAL_STOP_ERROR = "Stopped Manually!"

    # Default name for the HT 100 Precision model replied to T command
    DEFAULT_NAME = "HT:100P"

    # ################### Control commands ###################################
    # Clear OVERLOAD error
    CLEAR_ERROR = {"name": "C", "reply": {"type": str}}
    # Get status/error message
    GET_STATUS = {"name": "f", "reply": {"type": str, "parser": parser.researcher, "args": [r'FLT:\s(.*!)']}}
    # Identify the instrument (Flash the device display)
    IDENTIFY = {"name": "M", "reply": {"type": str}}
    # Get stirrer name
    GET_NAME = {"name": "T", "reply": {"type": str}}
    # Stop stirrer
    STOP = {"name": "R0000", "reply": {"type": int, "parser": parser.researcher, "args": [r'SET:\s(\d{1,4})']}}
    # Set rotation speed (rpm)
    SET_SPEED = {"name": "R", "type": int, "check": {"min": 10, "max": 2000},
                 "reply": {"type": int, "parser": parser.researcher, "args": [r'SET:\s(\d{1,4})']}}
    # Get rotation speed setpoint
    GET_SPEED_SET = {"name": "s", "reply": {"type": int, "parser": parser.researcher, "args": [r'SET:\s(\d{1,4})']}}
    # Get actual rotation speed
    GET_SPEED = {"name": "r", "reply": {"type": int, "parser": parser.researcher, "args": [r'RPM:\s(\d{1,4})']}}

    # Get torque (in Newton millimeter - Nmm)
    GET_TORQUE = {"name": "m", "reply": {"type": int, "parser": parser.researcher, "args": [r'NCM:\s(-*?\d{1,4})']}}
    # Switch remote control off; motor speed is controlled by knob position.
    # WARNING! If this command is issued while the stirrer is rotating, it reads
    # out actual knob position & applies according speed, it wouldn't stop!
    SET_RMT_OFF = {"name": "D"}

    # ################### Configuration commands #############################
    # Set zero reference for torque value
    SET_TORQ_ZERO = {"name": "N", "reply": {"type": str}}
    # Speed range I - no effect on HeiTorque100 model
    SET_MODE_I = {"name": "B"}
    # Speed range II - no effect on HeiTorque100 model
    SET_MODE_II = {"name": "A"}


class HeiTorque100PrecisionStirrer(AbstractStirringController):
    """
    This provides a Python class for the Heidolph Hei-TORQUE 100 Precision
    overhead stirrer based on the english section of the original
    operation manual 01-005-005-55-4, 15.08.2019.
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = HeiTorque100PrecisionStirrerCommands

        # connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = ""

        # Internal state variable
        # This stirrer lack explicit start/stop commands, so it starts as soon as you set non-zero speed
        self._speed_setpoint = 0
        self._running = False

    def parse_reply(self, cmd: Dict, reply: Any) -> Any:
        """Overloaded base class method to handle regex parsing.

        Args:
            reply: Reply from the device.
            cmd: Command definition toc heck for reply parsing workflow.

        Returns:
            (any): Parsed reply from the device.
        """

        # Handle standard parsing
        reply = super().parse_reply(cmd, reply)
        # If we parsed with regexp, extract first matched group from Regex match object
        if isinstance(reply, re.Match):  # type: ignore
            if reply is None:
                raise PLDeviceReplyError("Regular expression match failed on device reply!")
            reply = reply[1]
            self.logger.debug("parse_reply()::extracted regex result <%s>", reply)
            # Cast the right type
            return self.cast_reply_type(cmd, reply)
        return reply

    def initialize_device(self):
        """Performs device initialization & clear the errors.
        """

        # Blink the screen - visual aid
        self.identify()
        try:
            self.check_errors()
        except PLDeviceInternalError:
            self.clear_errors()
        self.logger.info("Device initialized.")

    def identify(self):
        """Blinks the screen.
        """

        self.send(self.cmd.IDENTIFY)

    @in_simulation_device_returns(HeiTorque100PrecisionStirrerCommands.NO_ERROR)
    def get_status(self) -> str:
        """ Gets device status.
        """

        return self.send(self.cmd.GET_STATUS)

    def check_errors(self):
        """Check device for errors & raises PLDeviceInternalError with
        appropriate error message.
        """

        status = self.get_status()
        if status == self.cmd.OVERHEAT_ERROR:
            errmsg = "Device overheat error!"
            self.logger.error(errmsg)
            raise PLDeviceInternalError(errmsg)
        if status == self.cmd.MOTOR_ERROR:
            errmsg = "Device motor error!"
            self.logger.error(errmsg)
            raise PLDeviceInternalError(errmsg)
        if status == self.cmd.OVERLOAD_ERROR:
            errmsg = "Device overload error!"
            self.logger.error(errmsg)
            raise PLDeviceInternalError(errmsg)
        if status == self.cmd.MANUAL_STOP_ERROR:
            errmsg = "Device manual stop error!"
            self.logger.error(errmsg)
            raise PLDeviceInternalError(errmsg)

    def clear_errors(self):
        """Clears device errors.
        """

        self.send(self.cmd.CLEAR_ERROR)

    @in_simulation_device_returns(HeiTorque100PrecisionStirrerCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """Checks whether device is connected.
        """

        try:
            reply = self.send(self.cmd.GET_NAME)
        except PLConnectionError:
            return False
        if self.cmd.DEFAULT_NAME in reply:
            return True
        self.logger.warning("Device name <%s> doesn't seem to match device model!", reply)
        return False

    def is_idle(self) -> bool:
        """Checks whether device is idle.
        """

        if not self.is_connected():
            return False
        ready = self.get_status()
        return ready == self.cmd.NO_ERROR and not self._running

    def start_stirring(self):
        """Starts rotation.
        """

        if self._speed_setpoint == 0:
            self.logger.warning("Starting device with zero speed makes no effect.")
            return
        self._running = True
        self.set_speed(self._speed_setpoint)

    @in_simulation_device_returns(0)
    def stop_stirring(self):
        """Stops rotation.
        """

        readback_setpoint = self.send(self.cmd.STOP)
        if readback_setpoint != 0:
            raise PLDeviceReplyError(f"Error stopping stirrer. Requested setpoint <{self._speed_setpoint}> RPM, "
                                     f"read back setpoint <{readback_setpoint}> RPM")
        self._running = False

    @in_simulation_device_returns("{$args[1]}")
    def set_speed(self, speed: int):
        """Sets rotation speed in rpm.
        """

        # If the stirrer is not running, just update internal variable
        if not self._running:
            # Check value against limits before updating
            self.check_value(self.cmd.SET_SPEED, speed)
            self._speed_setpoint = speed
        else:
            readback_setpoint = self.send(self.cmd.SET_SPEED, speed)
            if readback_setpoint != speed:
                self.stop()
                raise PLDeviceReplyError(f"Error setting stirrer speed. Requested setpoint <{self._speed_setpoint}> "
                                         f"RPM, read back setpoint <{readback_setpoint}> RPM")
            self._speed_setpoint = speed

    def get_speed(self) -> int:
        """Gets actual rotation speed in rpm.
        """

        return self.send(self.cmd.GET_SPEED)

    def get_speed_setpoint(self) -> int:
        """Gets desired rotation speed.
        """

        return self._speed_setpoint

    def get_torque(self) -> int:
        """Gets current torque value in Nmm.
        """

        return self.send(self.cmd.GET_TORQUE)

    def calibrate_torque(self):
        """Sets current measured torques to zero.
        """

        self.send(self.cmd.SET_TORQ_ZERO)
