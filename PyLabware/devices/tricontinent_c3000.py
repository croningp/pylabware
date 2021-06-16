"""PyLabware driver for Tricontinent С3000 syringe pump with integrated valve."""

from typing import Optional, Union, Dict, Any
import serial

# Core import
from .. import parsers as parser
from ..controllers import (AbstractSyringePump,
                           AbstractDistributionValve,
                           in_simulation_device_returns)
from ..exceptions import (PLConnectionError, PLDeviceCommandError,
                          PLDeviceError, PLDeviceInternalError,
                          PLDeviceReplyError)
from ..models import LabDeviceCommands, LabDeviceReply, ConnectionParameters


class C3000SyringePumpCommands(LabDeviceCommands):
    """Collection of command definitions for C3000 pump, DT protocol.
    """

    # ################### Configuration constants #############################

    # Mapping of rotary switch settings to apparent pump address on serial
    # Please, note, position F is not used (see p.23 of the manual)
    SWITCH_ADDRESSES = {
        "0": "1",
        "1": "2",
        "2": "3",
        "3": "4",
        "4": "5",
        "5": "6",
        "6": "7",
        "7": "8",
        "8": "9",
        "9": ":",
        "A": ";",
        "B": "<",
        "C": "=",
        "D": ">",
        "E": "?",
        "all": "-"
    }

    # Allowed valve positions
    # Y-valves, 90°-valves and T-valves use IOBE-notation
    # 6-pos valves use I1..I6/O1..O6 notation (I - moves CW, O - moves CCW)
    # 3-pos distribution valves can use either IOBE or I1..I3/O1..O3 depending how they were configured (Uxx command)
    VALVE_POSITIONS = (
        "",  # This is to pass check when IOBE addressing is used and I or O is requested
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    )

    # Valve types for Uxx command
    VALVE_TYPES = {
        "3PORT_Y": "1",  # IOBE control
        "3PORT_T": "5",  # IOBE control
        "3PORT_DISTR_IOBE": "4",  # IOBE control
        "3PORT_DISTR_IO": "11",  # I1..In, O1..On control
        "4PORT_90DEG": "2",  # IOBE control
        "4PORT_T": "5",  # IOBE control
        "4PORT_LOOP": "9",  # IOBE control
        "6PORT_DISTR": "7"  # I1..In, O1..On control
    }

    # Plunger motor resolution modes
    RESOLUTION_MODES = {
        "N0": 3000,  # Normal mode - power up default
        "N1": 24000,  # Positioning micro-increment mode
        "N2": 24000  # Positioning & velocity micro-increment mode
    }

    # Plunger motor ramp slope modes. Key - ramp code, Value - list of ramp slope in increments/sec^2 for N0-N1 and N2 modes
    RAMP_PLOPE_MODES = {
        "1": [2500, 20000],
        "2": [5000, 40000],
        "3": [7500, 60000],
        "4": [10000, 80000],
        "5": [12500, 100000],
        "6": [15000, 120000],
        "7": [17500, 140000],
        "8": [20000, 160000],
        "9": [22500, 180000],
        "10": [25000, 200000],
        "11": [27500, 220000],
        "12": [30000, 240000],
        "13": [32500, 260000],
        "14": [35000, 280000],  # Power-up default
        "15": [37500, 300000],
        "16": [40000, 320000],
        "17": [42500, 340000],
        "18": [45000, 360000],
        "19": [47500, 380000],
        "20": [50000, 400000]
    }

    # Plunger motor speed. Key - speed code, Value - list of speeds in steps/sec for N0-N1 and N2 modes
    SPEED_MODES = {
        "0": [6000, 48000],
        "1": [5600, 44800],
        "2": [5000, 40000],
        "3": [4400, 35200],
        "4": [3800, 30400],
        "5": [3200, 25600],
        "6": [2600, 20800],
        "7": [2200, 17600],
        "8": [2000, 16000],
        "9": [1800, 14400],
        "10": [1600, 12800],
        "11": [1400, 11200],  # Power-up default
        "12": [1200, 9600],
        "13": [1000, 8000],
        "14": [800, 6400],
        "15": [600, 4800],
        "16": [400, 3200],
        "17": [200, 1600],
        "18": [190, 1520],
        "19": [180, 1440],
        "20": [170, 1360],
        "21": [160, 1280],
        "22": [150, 1200],
        "23": [140, 1120],
        "24": [130, 1040],
        "25": [120, 960],
        "26": [110, 880],
        "27": [100, 800],
        "28": [90, 720],
        "29": [80, 640],
        "30": [70, 560],
        "31": [60, 480],
        "32": [50, 400],
        "33": [40, 320],
        "34": [30, 240],
        "35": [20, 160],
        "36": [18, 144],
        "37": [16, 128],
        "38": [14, 112],
        "39": [12, 96],
        "40": [10, 80]
    }

    # ## C3000 error codes ###
    # Error codes are represented as a bit field occupying 4 right-most bits of status byte, according to C3000 manual, page 90
    ERROR_CODES = {
        0b0000: "No error.",
        0b0001: "Initialization failure!",
        0b0010: "Invalid command!",
        0b0011: "Invalid operand!",
        0b0100: "Invalid checksum!",
        0b0110: "EEPROM failure!",
        0b0111: "Device not initialized!",
        0b1000: "CAN bus failure!",
        0b1001: "Plunger overload!",
        0b1010: "Valve overload!",
        0b1011: "Plunger move not allowed! Check valve position.",
        0b1111: "Command overflow!"
    }

    # Default status - pump initialized, idle, no error
    DEFAULT_STATUS = "/0`1"

    # ################### Control commands ###################################

    # ## Initialization commands ##
    # Initialize plunger & valves, valve numbering - CW from syringe (first on the left)
    # For non-distribution valves - set valve to the right
    INIT_ALL_CW = {"name": "Z", "reply": {"type": str}}
    # Initialize plunger & valves, valve numbering - CCW from syringe (first on the right)
    # For non-distribution valves - set valve to the left
    INIT_ALL_CCW = {"name": "Y", "reply": {"type": str}}
    # Initialize syringe only
    INIT_SYRINGE = {"name": "W", "reply": {"type": str}}
    # Initialize valve only
    INIT_VALVE = {"name": "w", "reply": {"type": str}}

    # ## Plunger movement commands ##
    # Move plunger to absolute position
    SYR_MOVE_ABS = {"name": "A", "reply": {"type": str}}
    # Move plunger to absolute position, do not set busy flag
    SYR_MOVE_ABS_NOBUSY = {"name": "a", "reply": {"type": str}}
    # Relative pick-up
    SYR_SUCK_REL = {"name": "P", "reply": {"type": str}}
    # Relative pick-up, do not set busy flag
    SYR_SUCK_REL_NOBUSY = {"name": "p", "reply": {"type": str}}
    # Relative dispense
    SYR_SPIT_REL = {"name": "D", "reply": {"type": str}}
    # Relative dispense, do not set busy flag
    SYR_SPIT_REL_NOBUSY = {"name": "d", "reply": {"type": str}}

    # ## Valve movement commands ##
    # Rotate valve to input position, or to position <n> clockwise (U11 configuration)
    VALVE_MOVE_I = {"name": "I", "check": {"values": VALVE_POSITIONS}, "reply": {"type": str}}
    # Rotate valve to output position, or to position <n> counter-clockwise (U11 configuration)
    VALVE_MOVE_O = {"name": "O", "check": {"values": VALVE_POSITIONS}, "reply": {"type": str}}
    # Rotate valve to bypass position. No check as there are no arguments.
    VALVE_MOVE_B = {"name": "B", "reply": {"type": str}}
    # Rotate valve to extra position. No check as there are no arguments.
    VALVE_MOVE_E = {"name": "E", "reply": {"type": str}}

    # ## Execution flow control commands ##
    # Execute command string
    PRG_RUN = {"name": "R", "reply": {"type": str}}
    # Repeat last command
    PRG_RPT_LAST = {"name": "X", "reply": {"type": str}}
    # Store program string into EEPROM
    PRG_EEPROM_ST = {"name": "s", "reply": {"type": str}}
    # Execute program string from EEPROM
    PRG_EEPROM_EXEC = {"name": "e", "reply": {"type": str}}
    # Mark start of looped command sequence
    PRG_MARK_LOOP_START = {"name": "g"}
    # Mark end of looped command sequence
    PRG_MARK_LOOP_END = {"name": "G"}
    # Delay command execution
    PRG_DELAY_EXEC = {"name": "M"}
    # Halt command execution (wait for R command and/or ext. input change)
    PRG_HALT = {"name": "H", "reply": {"type": str}}
    # Terminate commands execution
    PRG_TERM = {"name": "T", "reply": {"type": str}}

    # ## Report commands ##
    # Query pump status
    GET_STATUS = {"name": "?Q", "reply": {"type": str}}
    # Query firmware version
    GET_FW_VER = {"name": "?23", "reply": {"type": str}}
    # Query EEPROM data
    GET_EEPROM_DATA = {"name": "?27", "reply": {"parser": parser.slicer, "args": [5]}}
    # Query initialized status
    GET_INIT_STATUS = {"name": "?19", "reply": {"type": bool}}
    # Query plunger absolute position
    GET_SYR_POS = {"name": "?", "reply": {"type": int}}
    # Query start velocity
    GET_START_VEL = {"name": "?1", "reply": {"type": str}}
    # Query maximum velocity
    GET_MAX_VEL = {"name": "?2", "reply": {"type": str}}
    # Query cut-off velocity
    GET_STOP_VEL = {"name": "?3", "reply": {"type": str}}
    # Query acceleration/deceleration ramp
    GET_STEP_RAMP = {"name": "?7", "reply": {"type": str}}
    # Query backlash increments setting
    GET_BACK_INC = {"name": "?12", "reply": {"type": str}}
    # Query motor hold current
    GET_MOT_HOLD = {"name": "?25", "reply": {"type": str}}
    # Query motor run current
    GET_MOT_RUN = {"name": "?26", "reply": {"type": str}}
    # Query valve position
    GET_VALVE_POS = {"name": "?6", "reply": {"type": str, "parser": str.upper}}

    # ################### Configuration commands #############################

    # ## Configuration commands ##
    # Set pump configuration (valve configuration, autorun, etc)
    SET_PUMP_CONF = {"name": "U"}
    # Set system configuration (factory calibrations)
    SET_CALIB_CONF = {"name": "u"}
    # Set internal position counter
    SET_POS_CTR = {"name": "z", "reply": {"type": str}}
    # Set syringe gap volume
    SET_SYR_GAP = {"name": "R", "reply": {"type": str}}
    # Set backlash increments
    SET_BACK_INC = {"name": "K", "reply": {"type": str}}
    # Set acceleration/deceleration ramp slope
    SET_RAMP_PLOPE = {"name": "L", "type": str, "check": {"values": RAMP_PLOPE_MODES.keys()}}
    # Set start velocity (beginning of ramp)
    SET_START_VEL = {"name": "v", "type": int, "check": {"min": 1, "max": 8000}, "reply": {"type": str}}
    # Set maximum velocity (top of ramp) in increments/second
    SET_MAX_VEL = {"name": "V", "type": int, "check": {"min": 1, "max": 48000}, "reply": {"type": str}}
    # Set maximum velocity (top of ramp) with velocity code
    SET_MAX_VEL_CODE = {"name": "S", "type": str, "check": {"values": SPEED_MODES.keys()}, "reply": {"type": str}}
    # Set cut-off velocity (end of ramp)
    SET_STOP_VEL = {"name": "c", "type": int, "check": {"min": 1, "max": 21600}, "reply": {"type": str}}
    # Set number of motor steps for cut-off
    SET_STOP_STEPS = {"name": "C", "reply": {"type": str}}
    # Set resolution (stepping mode)
    SET_RES_MODE = {"name": "N", "type": str, "check": {"values": RESOLUTION_MODES.keys()}, "reply": {"type": str}}
    # Set external outputs
    SET_EXT_OUT = {"name": "J", "reply": {"type": str}}
    # Set external outputs when syringe is at certain position
    SET_EXT_OUT_COND = {"name": "j", "reply": {"type": str}}
    # Set motor hold current
    SET_MOT_HOLD = {"name": "h", "reply": {"type": str}}
    # Set motor run current
    SET_MOT_RUN = {"name": "m", "reply": {"type": str}}


class C3000SyringePump(AbstractSyringePump, AbstractDistributionValve):
    """
    This provides a Python class for the Tricontinent C3000 syringe pump
    based on the the original operation manual 8694-12 E
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int],
                 switch_address: Optional[Union[int, str]] = None, valve_type: str = "3PORT_DISTR_IOBE"):
        """Default constructor.
        """

        # Load commands from helper class
        self.cmd = C3000SyringePumpCommands

        # Check that valid valve type has been passed
        try:
            self._valve_type = C3000SyringePumpCommands.VALVE_TYPES[valve_type]
        except KeyError:
            raise PLDeviceError("Invalid valve type <{}> provided!".format(valve_type)) from None

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        # TCP/IP relevant settings
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        # RS-232/RS-485 relevant settings
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE

        super().__init__(device_name, connection_mode, connection_parameters)

        # Set switch address
        try:
            switch_address = self.cmd.SWITCH_ADDRESSES[str(switch_address)]
        except KeyError:
            raise PLDeviceError("Invalid switch address <{}> supplied!".format(switch_address)) from None

        # Protocol settings
        self.command_prefix = "/" + switch_address
        # Run commands after sending them to pump by default (R appended)
        self.command_terminator = self.cmd.PRG_RUN["name"] + "\r\n"
        self.reply_prefix = "/0"
        self.reply_terminator = "\x03\r\n"
        self.args_delimiter = ""
        # Pump status byte
        self._last_status = 0

    @property
    def autorun(self):
        """Property showing if the commands should be executed immediately,
        or queued instead.
        """

        return self.cmd.PRG_RUN["name"] in self.command_terminator

    @autorun.setter
    def autorun(self, value):
        """Setter for the autorun property.
        """

        if value is True:
            self.command_terminator = self.cmd.PRG_RUN["name"] + "\r\n"
        else:
            self.command_terminator = "\r\n"

    def parse_reply(self, cmd: Dict, reply: Any) -> str:
        """Overloaded method from base class. We need to do some more
        complex processing here for the status byte manipulations.
        """

        # Strip reply terminator and prefix
        reply = parser.stripper(reply.body, self.reply_prefix, self.reply_terminator)
        # Then analyze status byte
        # Status byte is the 1st byte of reply string, & we need it's byte code.
        self._last_status = ord(reply[0])
        self.check_errors()
        self.logger.debug("parse_reply()::status byte checked, invoking parsing on <%s>", reply[1:])
        # Chop off status byte & do standard processing
        return super().parse_reply(cmd, reply[1:])

    def check_errors(self):
        """Checks error bits in the status byte of the pump reply.
        """

        self.logger.debug("check_errors()::checking errors on byte <%s>", self._last_status)
        # Error code is contained in 4 right-most bytes,
        # so we need to chop off the rest
        error_code = self._last_status & 0b1111
        # No error
        if error_code == 0:
            return None
        try:
            raise PLDeviceInternalError(self.cmd.ERROR_CODES[error_code])
        except KeyError:
            # This shouldn't really happen, means that pump replied with
            # error code not in the ERROR_CODES dictionary
            # (which completely copies the manual)
            raise PLDeviceReplyError("Unknown error! Status byte: {}".format(bin(self._last_status)))

    def is_connected(self) -> bool:
        """Checks whether the device is connected by
        checking it's firmware version.
        """

        try:
            version = self.send(self.cmd.GET_FW_VER)
            self.logger.debug("is_connected()::Device connected; FW version <%s>", version)
            return True
        except PLConnectionError:
            return False

    def get_status(self):
        """Not supported on this device.
        """
        # TODO implement through status byte analysis

    def clear_errors(self):
        """Happens automatically upon errors read-out,
        except those requiring pump re-initialization.
        """

    def initialize_device(self, valve_enumeration_direction="CW", input_port=None, output_port=None):
        """Runs pump initialization.
        """

        # Select appropriate command depending on the direction
        if valve_enumeration_direction == "CW":
            cmd = self.cmd.INIT_ALL_CW
        elif valve_enumeration_direction == "CCW":
            cmd = self.cmd.INIT_ALL_CCW
        else:
            raise PLDeviceCommandError("Invalid direction for valve initialization provided!")

        # Initialization arguments. First - plunger initialization
        # power(we are not using it).
        # Second - number of input port for initialization (0 - default).
        # Third - number of output port for initialization (0 - default).
        # Second and third arguments are ignored for non-distribution valves
        # (as been set by Ux command)
        arglist = [""]

        # Check if we are asked to use specific input/output ports.
        # Otherwise they will be first(I) and last(O) for CW init or
        # last(I) and first(O) for CCW init
        for port in [input_port, output_port]:
            if port is not None:
                if port not in self.cmd.VALVE_POSITIONS:
                    raise PLDeviceCommandError("Invalid port for initialization was provided!")
                arglist.append(port)

        # Glue arguments to the command they should be
        # comma-separated list (0,0,0)
        args = ",".join(str(a) for a in arglist)

        # Send commands & check errors in the reply
        self.send(cmd, args)

        self.logger.info("Device initialized.")

    @in_simulation_device_returns(True)
    def is_initialized(self) -> bool:
        """Check if pump has been initialized properly after power-up.
        """

        try:
            initialized = self.send(self.cmd.GET_INIT_STATUS)
            return initialized
        except PLConnectionError:
            return False

    @in_simulation_device_returns(LabDeviceReply(body=C3000SyringePumpCommands.DEFAULT_STATUS))
    def is_idle(self) -> bool:
        """Checks if pump is in idle state.
        """

        # Send status request command and read back reply with no parsing
        # Parsing manipulates status byte to get error flags, we need it here
        try:
            _ = self.send(self.cmd.GET_STATUS)
        except PLConnectionError:
            return False
        # Busy/idle bit is 6th bit of the status byte. 0 - busy, 1 - idle
        if self._last_status & 1 << 5 == 0:
            self.logger.debug("is_idle()::false.")
            return False
        # Check for errors if any
        # TODO check if this behavior is consistent with other devices
        # i.e. having errors <-> being idle
        try:
            self.check_errors()
        except PLDeviceInternalError:
            self.logger.debug("is_idle()::false, errors present.")
            return False
        self.logger.debug("is_idle()::true.")
        return True

    def start(self):
        """Starts program execution."""

        if self.autorun is True:
            self.logger.warning("Sending run command with autorun enabled is not required.")
            return
        self.send(self.cmd.PRG_RUN)

    def stop(self):
        """ Stops executing current program/action immediately."""

        self.send(self.cmd.PRG_TERM)

    def set_speed(self, speed: int):
        """Sets maximum velocity (top of the ramp) for the syringe motor.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_MAX_VEL, int(speed))

    def get_speed(self):
        raise NotImplementedError("Getting speed is not supported on this model.")

    def set_predefined_speed(self, velocity_code: int):
        """Sets maximum velocity (top of the ramp) for the syringe motor.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_MAX_VEL_CODE, velocity_code)

    def move_home(self):
        self.move_plunger_absolute(0)

    def move_plunger_absolute(self, position: int, set_busy: bool = True):
        """Makes absolute plunger move.
        """

        if set_busy is True:
            cmd = self.cmd.SYR_MOVE_ABS
        else:
            cmd = self.cmd.SYR_MOVE_ABS_NOBUSY
        # Send command & check reply for errors
        self.execute_when_ready(self.send, cmd, position)

    def get_plunger_position(self) -> int:
        """Returns absolute plunger position.
        """

        # Send command & check reply for errors
        return self.send(self.cmd.GET_SYR_POS)

    def move_plunger_relative(self, position: int, set_busy: bool = True):
        """Makes relative plunger move. This is a wrapper for
        dispense()/withdraw().
        """

        position = int(position)
        if position > 0:
            return self.withdraw(position, set_busy)
        return self.dispense(abs(position), set_busy)

    def dispense(self, increments: float, set_busy: bool = True):
        """Makes relative dispense.
        """

        if set_busy is True:
            cmd = self.cmd.SYR_SPIT_REL
        else:
            cmd = self.cmd.SYR_SPIT_REL_NOBUSY

        # Send command & check reply for errors
        self.execute_when_ready(self.send, cmd, increments)

    def withdraw(self, increments: float, set_busy: bool = True):
        """Makes relative aspiration.
        """

        if set_busy is True:
            cmd = self.cmd.SYR_SUCK_REL
        else:
            cmd = self.cmd.SYR_SUCK_REL_NOBUSY
        # Send command & check reply for errors
        self.execute_when_ready(self.send, cmd, increments)

    def set_valve_position(self, requested_position: str):
        """Sets the distribution valve position.
        """

        requested_position = str(requested_position)
        # We have to distinguish between IOBE and In/On valve position addressing
        # & check it against current valve type
        if len(requested_position) == 1:
            # IOBE addressing allowed for all but 6-way distribution valves
            if self._valve_type == self.cmd.VALVE_TYPES["6PORT_DISTR"]:
                self.logger.warning("Requested valve position doesn't seem to match valve type installed.")
        elif len(requested_position) == 2:
            # In/On addressing is allowed only for 6-way valves and 3-way valves.
            if self._valve_type not in [self.cmd.VALVE_TYPES["3PORT_DISTR_IO"], self.cmd.VALVE_TYPES["6PORT_DISTR"]]:
                self.logger.warning("Requested valve position doesn't seem to match valve type installed.")

        # The position requested is the actual command we have to send to the pump.
        # But we need to match it against a defined command.
        if requested_position[:1] == "I":
            cmd = self.cmd.VALVE_MOVE_I
        elif requested_position[:1] == "O":
            cmd = self.cmd.VALVE_MOVE_O
        elif requested_position == "B":
            cmd = self.cmd.VALVE_MOVE_B
        elif requested_position == "E":
            cmd = self.cmd.VALVE_MOVE_E
        else:
            raise PLDeviceCommandError(f"Unknown valve position <{requested_position}> requested!")

        # Get numeric position (if I1..I6/O1..O6 notation is used)
        args = requested_position[1:]

        # Send command & check reply for errors
        self.execute_when_ready(self.send, cmd, args)

    def get_valve_position(self) -> str:
        """Reads current position of the valve.
        """

        # Send command & check reply for errors
        return self.send(self.cmd.GET_VALVE_POS)

    def set_ramp_slope(self, ramp_code: str):
        """Sets slope of acceleration/deceleration ramp for the syringe motor.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_RAMP_PLOPE, ramp_code)

    def set_start_velocity(self, start_velocity: int):
        """Sets starting velocity for the syringe motor.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_START_VEL, start_velocity)

    def set_stop_velocity(self, stop_velocity: int):
        """Sets stopping velocity for the syringe motor.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_STOP_VEL, stop_velocity)

    def set_resolution_mode(self, resolution_mode: str):
        """Sets plunger resolution mode.
        """

        # Send command & check reply for errors
        self.send(self.cmd.SET_RES_MODE, resolution_mode)

    def set_valve_type(self, valve_type: str, confirm: bool = False):
        """Sets valve type. This command requires power-cycle to activate new settings!
        """

        self.logger.warning("Changing the valve type would require power-cycling the pump!")
        if confirm is not True:
            self.logger.info("Please, execute set_valve_type(valve_type, confirm=True)"
                             "to write new valve configuration to pump EEPROM.")
            return
        try:
            # Get correct valve code
            self._valve_type = C3000SyringePumpCommands.VALVE_TYPES[valve_type]
        except KeyError:
            raise PLDeviceCommandError("Invalid valve type requested!")
        # Send command & check reply for errors
        self.send(self.cmd.SET_PUMP_CONF, self._valve_type)
        self.logger.info("Valve type updated successfully. Don't forget to power-cycle the pump!")

    def get_pump_configuration(self):
        """Reads pump EEPROM configuration.
        """
        # Send command & check reply for errors
        return self.send(self.cmd.GET_EEPROM_DATA)
