"""PyLabware driver for the PL-series Power Supply
"""

from typing import Dict, Union, Optional

from .. import parsers as parser
from ..controllers import LabDevice
from ..exceptions import SLConnectionError
from ..models import LabDeviceCommands

# Regex consts for this device
INT_REGEX = r"\d[0-9]{1,}"
FLOAT_REGEX = r"\d[+-]?([0-9]*[.])?[0-9]+"


class PLPowerSupplyCommands(LabDeviceCommands):
    """Commands for the PL series Power Supply as detailed in documentation.
    """

    # Instrument Specific Commands
    SET_OUTPUT_VOLTAGE = {"name": "V{first} {second}", "type": float}

    SET_OUTPUT_VOLTAGE_WITH_VERIFY = {
        "name": "V{first}V {second}", "type": float
    }

    SET_OUTPUT_OVER_VOLTAGE_PROTECTION_TRIP_POINT = {
        "name": "OVP{first} {second}", "type": float
    }

    SET_OUTPUT_CURRENT_LIMIT = {"name": "I{first} {second}", "type": float}

    SET_OUTPUT_OVER_CURRENT_PROTECTION_TRIP_POINT = {
        "name": "OCP{first} {second}", "type": float
    }

    GET_OUTPUT_VOLTAGE = {
        "name": "V{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_CURRENT = {
        "name": "I{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_VOLTAGE_TRIP_SETTING = {
        "name": "OVP{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_CURRENT_TRIP_SETTING = {
        "name": "OCP{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_READBACK_VOLTAGE = {
        "name": "V{first}O?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_READBACK_CURRENT = {
        "name": "I{first}O?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    SET_OUTPUT_CURRENT_RANGE = {
        "name": "IRANGE{first} {second}", "type": int
    }

    GET_OUTPUT_CURRENT_RANGE = {
        "name": "IRANGE{first}?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_OUTPUT_VOLTAGE_STEP_SIZE = {
        "name": "DELTAV{first} {second}", "type": float
    }

    SET_OUTPUT_CURRENT_STEP_SIZE = {
        "name": "DELTAI{first} {second}", "type": float
    }

    GET_OUTPUT_VOLTAGE_STEP_SIZE = {
        "name": "DELTAV{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    GET_OUTPUT_CURRENT_STEP_SIZE = {
        "name": "DELTAI{first}?",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [FLOAT_REGEX]
        }
    }

    INCREMENT_OUTPUT_VOLTAGE = {"name": "INCV{first}"}

    INCREMENT_OUTPUT_VOLTAGE_WITH_VERIFY = {"name": "INCV{first}V"}

    DECREMENT_OUTPUT_VOLTAGE = {"name": "DECV{first}"}

    DECREMENT_OUTPUT_VOLTAGE_WITH_VERIFY = {"name": "DECV{first}V"}

    INCREMENT_OUTPUT_CURRENT = {"name": "INCI{first}"}

    DECREMENT_OUTPUT_CURRENT = {"name": "DECI{first}"}

    SET_OUTPUT = {"name": "OP{first} {second}", "type": int}

    SET_ALL_OUTPUTS = {"name": "OPALL {second}", "type": int}

    GET_OUTPUT_STATUS = {
        "name": "OP{first}?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    CLEAR_TRIP_CONDITIONS = {"name": "TRIPRST"}

    QUERY_AND_CLEAR_LIMIT_EVENT_STATUS_REGISTER = {
        "name": "LSR{first}?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_LIMIT_EVENT_STATUS_ENABLE_REGISTER = {
        "name": "LSE{first} {second}", "type": int
    }

    GET_LIMIT_EVENT_STATUS_ENABLE_REGISTER = {
        "name": "LSE{first}?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SAVE_OUTPUT_SETUP = {"name": "SAV{first} {second}", "type": int}

    RECALL_OUTPUT_SETUP = {"name": "RCL{first} {second}", "type": int}

    # System and Status Commands
    CLEAR_STATUS = {"name": "*CLS"}

    QUERY_AND_CLEAR_EXECUTION_ERROR_REGISTER = {
        "name": "EER?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_STANDARD_EVENT_ENABLE_REGISTER = {"name": "*ESE {second}", "type": float}

    GET_STANDARD_EVENT_ENABLE_REGISTER = {
        "name": "*ESE?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    GET_STANDARD_EVENT_ENABLE_REGISTER_AND_CLEAR = {
        "name": "*ESR?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    GET_IST_LOCAL_MESSAGE = {
        "name": "*IST?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_OPERATION_COMPLETE_BIT = {"name": "*OPC"}

    GET_OPERATION_COMPLETE_BIT = {
        "name": "*OPC?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_PARALLEL_POLL_ENABLE_REGISTER = {"name": "*PRE {second}", "type": int}

    GET_PARALLEL_POLL_ENABLE_REGISTER = {
        "name": "*PRE?", "reply": {"type": int}
    }

    QUERY_AND_CLEAR_QUERY_ERROR_REGISTER = {
        "name": "QER?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    SET_SERVICE_REQUEST_ENABLE_REGISTER = {"name": "*SRE {second}", "type": int}

    GET_SERVICE_REQUEST_ENABLE_REGISTER = {
        "name": "*SRE?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    GET_STATUS_BYTE_REGISTER = {
        "name": "*STB?",
        "reply": {
            "type": int,
            "parser": parser.researcher,
            "args": [INT_REGEX]
        }
    }

    WAIT_FOR_OPERATION_COMPLETE = {"name": "*WAI"}

    # Interface Management Commands
    # Note::These are added here but unused
    REQUEST_INSTRUMENT_LOCK = {"name": "IFLOCK", "reply": {"type": str}}

    REQUEST_INSTRUMENT_LOCK_STATUS = {
        "name": "IFLOCK?", "reply": {"type": str}
    }

    RELEASE_INSTRUMENT_LOCK = {"name": "IFUNLOCK", "reply": {"type": str}}

    GET_BUS_ADDRESS = {"name": "ADDRESS?", "reply": {"type": str}}

    GET_IP_ADDRESS = {"name": "IPADDR?", "reply": {"type": str}}

    GET_NET_MASK = {"name": "NETMASK?", "reply": {"type": str}}

    GET_NET_CONFIG = {"name": "NETCONFIG?", "reply": {"type": str}}


# Errors for the device
# Note::Error code for interlah hardware error is actually 1-9 but dicts
# cant support ranges as keys so it's -1 in this case
PL_POWER_SUPPLY_ERRORS = {
    -1: "Internal Hardware Error",
    100: "Range Error. Value not allowed",
    101: "Setup data corrupted",
    102: "No setup data to recall",
    103: "Attemtped read/write on unavailable output",
    104: "Invalid command or active output. Turn the output off first",
    200: "Read only: cannot write setting"
}


class Register:
    """Simple class to represent a bit register.

    Args:
        status (int): Status valuet hat is converted to bits
    """

    def __init__(self, status: int):
        self.value = status

        # Set attributes for each bit from LSB to MSB, converting to bool
        for i in range(8):
            setattr(self, f"bit{i}", bool((self.value >> i) & 1))


class StatusRegister(Register):
    """Class to represent a PL Power Supply StatusRegister.
    Defined as a subclass of Register as there can be multiple different
    register types.

    Inherits:
        Register: Base register class

    Args:
        value (int): Status value
    """

    def __init__(self, value: int):
        super().__init__(value)

    @property
    def power_on(self) -> bool:
        """Determines if the power is on or not

        Returns:
            bool: Power On bit is set.
        """

        return self.bit7

    @property
    def command_error(self) -> bool:
        """Checks if the command error bit is set

        Returns:
            bool: Command Error bit is set.
        """

        return self.bit5

    @property
    def execution_error(self) -> bool:
        """Checks if the execution error bit has been set.

        Returns:
            bool: Execution error bit has been set.
        """

        return self.bit4

    @property
    def timeout_error(self) -> bool:
        """Checks if the timeout error bit is set.

        Returns:
            bool: Timeout error bit is set.
        """

        return self.bit3

    @property
    def query_error(self) -> bool:
        """Checks if the query error bit is set.

        Returns:
            bool: Query error bit is set.
        """

        return self.bit2

    @property
    def operation_complete(self) -> bool:
        """Checks if the operation complete bit is set

        Returns:
            bool: Operation complete bit is set.
        """

        return self.bit0


class PLPowerSupply(LabDevice):
    """Class for the PL Power Supply Series.

    Device operates by setting values for certain channels (Outputs) on the
    device. These outputs are as follows:
        `1`: 'Master' output (extreme right hand output)
        `2`: 'Slave' output in the four QMD/QMT modes
        `3`: Independent output on extreme left hand side

    Certain supplies may only have one output present. In that case, the output
    is `1` (Master).

    Commands that use the `with_verification` tag, the operation is completed
    when the value being set is within +/- 5% or +/- 10 counts, whichever is
    greater.

    Args:
        device_name (str): Name of the device
        conneciton_mode (str): Type of connection
        address (str): Address of the device
        port: (Union[str, int]): Port for the device
        auto_connect (bool): Connect automatically
    """
    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        address: str,
        port: Union[str, int],
        auto_connect: bool
    ):
        connection_parameters = {
            "port": port,
            "address": address
        }

        super().__init__(
            device_name=device_name,
            connection_mode=connection_mode,
            connection_parameters=connection_parameters,
            auto_connect=auto_connect
        )

        self.cmds = PLPowerSupplyCommands
        self.command_terminator = "\n"
        self.reply_terminator = "\r\n"

    @property
    def name(self) -> str:
        """Name of the device

        Returns:
            str: name of the device
        """

        return self.name

    def send(self, cmd, message, parse_reply=True):
        """This method takes the command to be sent and runs all necessary
        checks on the command parameter if present and required. Then the
        command get wrapped with the necessary prefix/terminator and connection
        lock is acquired. The command string is sent to the device using
        appropriate connection adapter and _recv() is invoked if a reply is
        expected. Only after that the connection lock is released.

        This method normally shouldn't be redefined in child classes.

        Args:
            cmd: The command to send.
            value: Command parameter, if any.
            prepare: If the command preparation is required.
            parse_reply: If the reply parsing is required.
        """

        if self._simulation is True:
            self.logger.info("SIM :: Pretending to send message <%r>", message)
            return None

        # Check if we need to get reply back for this command
        reply_expected = cmd.get("reply", False)

        with self._lock:
            self.connection.transmit(message)
            self.logger.info("Sent message <%r>", message)
            if reply_expected:
                result = self._recv(cmd, parse_reply)

                if result is not None:
                    return result[0]
                return result

    def prepare_message(
        self,
        cmd: Dict,
        first: int,
        second: Optional[Union[float, int]] = None
    ) -> Dict:
        """Prepares a message to be sent to the device.
        Replaces all placeholder strings in the command with appropriate values.

        Args:
            cmd (Dict): Command to send

            first (int): First argument (Output or value)

            second (Optional[Union[float, int]], optional): Second argument.
            Defaults to None.

        Returns:
            Dict: Formatted command
        """

        # Convert the args to strings if present
        first = str(first) if first is not None else first
        second = str(second) if second is not None else second

        # Replace placeholders with appropriate args
        if "{first}" in cmd["name"]:
            cmd["name"] = cmd["name"].replace("{first}", first)

        if "{second}" in cmd["name"]:
            cmd["name"] = cmd["name"].replace("{second}", second)

        # Format the command
        return self.command_prefix + cmd["name"] + self.command_terminator

    def check_value_range(self, value: int, lower: int, upper: int) -> bool:
        """Checks a value is within a specific range

        Args:
            value (int): Value to check
            lower (int): Lower bounds
            upper (int): Upper bounds

        Returns:
            bool: Within range or not
        """

        return value in range(lower, upper)

    def send_command_for_output(
        self,
        cmd: Dict,
        output: int,
        value: Optional[Union[float, int]] = None
    ) -> Optional[Union[float, int]]:
        """Sends a command that communicates with an output on the device

        Args:
            cmd (Dict): Command to send
            output (int): Input to send command for
            value (Union[float, int]): Value if needed, else None

        Returns:
            Optional[Union[float, int]]: Response if any
        """

        # Raise warning if output not in range and do nothing
        if not self.check_value_range(output, 1, 4):
            self.logger.error(
                f"Output {output} not in range [1-3] - Doing nothing."
            )
            return

        # Prepare messag before hand and send
        msg = self.prepare_message(cmd, first=output, second=value)
        return self.send(cmd, msg)

    def send_generic_command(
        self,
        cmd: Dict,
        first: Optional[Union[int, float]] = None,
        second: Optional[Union[int, float]] = None,
    ) -> Optional[Union[int, float]]:
        """Send a generic command to device with optional value
        Meant for commands where an output doesn't need validated.

        Args:
            cmd (Dict): Command to send
            first: Optional[Union[int, float]]: First parameter
            second: Optional[Union[int, float]]: Second Parameter

        Returns:
            Optional[Union[int, float]]: Response, if any
        """

        # Prepare the message before hand
        message = self.prepare_message(cmd, first=first, second=second)

        # Send command
        return self.send(cmd, message)

    def is_connected(self) -> bool:
        """Checks for a response from the device

        Returns:
            bool: Device is connected or not
        """

        try:
            reply = self.send_generic_command(
                self.cmds.GET_OUTPUT_STATUS, first=1
            )
        except SLConnectionError:
            return False

        if reply is None or not self.check_value_range(reply, 0, 2):
            return False

        return True

    def set_voltage(self, output: int, volts: float):
        """Sets the voltage for a given output

        Args:
            output (int): Output to use [1, 2, or 3]
            volts (float): Voltage to set
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_VOLTAGE, output, value=volts
        )

    def set_voltage_with_verification(
        self, output: int, volts: float
    ):
        """Sets the voltage for an output whilst waiting for verification
        that voltage has been achieved

        Args:
            output (int): Output to use [1, 2, or 3]
            volts (float): Voltage to set
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_VOLTAGE_WITH_VERIFY, output, value=volts
        )

    def set_voltage_over_protection_point(
        self, output: int, volts: float
    ):
        """Sets the voltage over the protection point for a given output

        Args:
            output (int): Output to use [1, 2, or 3]
            volts (float): Voltage
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_OVER_VOLTAGE_PROTECTION_TRIP_POINT,
            output,
            value=volts
        )

    def set_current_limit(self, output: int, current: float):
        """Sets the current limit for a given output

        Args:
            output (int): Output to use [1, 2, or 3]
            current (float): Current limit to set (in Amps).
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_CURRENT_LIMIT, output, value=current
        )

    def set_current_over_protection_point(
        self, output: int, current: float
    ):
        """Sets the current over the protection limit for a given output

        Args:
            output (int): Output to use [1, 2, or 3]
            current (float): Current to set (in Amps)
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_OVER_CURRENT_PROTECTION_TRIP_POINT,
            output,
            value=current
        )

    def get_voltage(self, output: int) -> float:
        """Gets the voltage for a given output

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Voltage for the output
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_VOLTAGE, output=output
        )

    def get_current(self, output: int) -> float:
        """Gets the current for the given output

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Current for the output (in Amps)
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_CURRENT, output
        )

    def get_voltage_trip_setting(self, output: int) -> float:
        """Get the voltage trip setting for an output in Volts

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Voltage trip setting.
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_VOLTAGE_TRIP_SETTING, output
        )

    def get_current_trip_setting(self, output: int) -> float:
        """Gets the current trip setting for an output in Amps

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Current trip setting (in Amps).
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_CURRENT_TRIP_SETTING, output
        )

    def get_readback_voltage(self, output: int) -> float:
        """Gets the Readback voltage for an output in volts.

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Readback voltage in volts.
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_READBACK_VOLTAGE, output
        )

    def get_readback_current(self, output: int) -> float:
        """Gets the readback current for an output in Amps.

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            float: Readback current in Amps.
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_READBACK_CURRENT, output
        )

    def set_current_range(self, output: int, range_value: int):
        """Sets the current range for an output.
        Checks the range is either:
            1: Low (500-800mA)
            2: High

        Args:
            output (int): Output to use [1, 2, or 3]
            range_value (int): Range setting
        """

        # Set the range to LOW (1) if it's out of bounds
        if not self.check_value_range(range_value, 1, 2):
            self.logger.warning(
                f"Range {range_value} should be 1 for low or 2 for high!\
 Defaulting to low"
            )
            range_value = 1

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_CURRENT_RANGE, output, value=range_value
        )

    def get_current_range(self, output: int) -> int:
        """Gets the current range for an output.
        Current range:
            1: Low (500-800mA)
            2: High

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            int: Current range either 1 or 2
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_CURRENT_RANGE, output
        )

    def set_voltage_step_size(self, output: int, voltage_step_size: float):
        """Set the voltage step size for incrementing voltage for an output

        Args:
            output (int): Output to use [1, 2, or 3]
            voltage_step_size (float): Step size in volts
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_VOLTAGE_STEP_SIZE,
            output,
            value=voltage_step_size
        )

    def set_current_step_size(self, output: int, current_step_size: float):
        """Set the current step size for incrementing current for an output

        Args:
            output (int): Output to use [1, 2, or 3]
            current_step_size (float): Step size in Amps
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT_CURRENT_STEP_SIZE,
            output,
            value=current_step_size
        )

    def increment_voltage(self, output: int):
        """Increment the voltage for an output

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.INCREMENT_OUTPUT_VOLTAGE, output
        )

    def increment_voltage_with_verification(self, output: int):
        """Increments the voltage by step_size for an output and waits for
        verification that the voltage has been achieved.

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.INCREMENT_OUTPUT_VOLTAGE_WITH_VERIFY, output
        )

    def increment_current(self, output: int):
        """Increments the current for an output by step_size for an output

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.INCREMENT_OUTPUT_CURRENT, output
        )

    def decrement_voltage(self, output: int):
        """Decrements the voltage for an output by step_size

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.DECREMENT_OUTPUT_VOLTAGE, output
        )

    def decrement_voltage_with_verification(self, output: int):
        """Decrements the voltage for an output by step_size and waits for
        verification that the voltage has been achieved.

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.DECREMENT_OUTPUT_VOLTAGE_WITH_VERIFY, output
        )

    def decrement_current(self, output: int):
        """Decrements the current for an output by step_size

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.DECREMENT_OUTPUT_CURRENT, output
        )

    def turn_output_on(self, output: int):
        """Switches an output on.

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT, output, value=1
        )

    def turn_output_off(self, output: int):
        """Switches an output off

        Args:
            output (int): Output to use [1, 2, or 3]
        """

        self.send_command_for_output(
            self.cmds.SET_OUTPUT, output, value=0
        )

    def turn_all_outputs_on(self):
        """Switches all outputs on
        """

        self.send_generic_command(
            self.cmds.SET_ALL_OUTPUTS, second=1
        )

    def turn_all_outputs_off(self):
        """Switches all outputs off
        """

        self.send_generic_command(
            self.cmds.SET_ALL_OUTPUTS, second=0
        )

    def get_output_status(self, output: int) -> int:
        """Gets the status of an output.
        Either:
            1: ON
            0: OFF

        Args:
            output (int): Output to use [1, 2, or 3]

        Returns:
            int: Status either 0 (OFF) or 1 (ON)
        """

        return self.send_command_for_output(
            self.cmds.GET_OUTPUT_STATUS, output
        )

    def clear_all_trip_conditions(self):
        """Clears all trip conditions for the device
        """

        self.send_generic_command(
            self.cmds.CLEAR_TRIP_CONDITIONS
        )

    def wait_for_operation_complete(self):
        """Waits for an operation to complete
        """

        self.send_generic_command(
            self.cmds.WAIT_FOR_OPERATION_COMPLETE
        )

    def clear_status(self):
        """Clears the status of the device, clearing the Status Byte Register.
        """

        self.send_generic_command(
            self.cmds.CLEAR_STATUS
        )

    def set_operation_complete(self):
        """Sets the operation compelte bit
        """

        self.send_generic_command(
            self.cmds.SET_OPERATION_COMPLETE_BIT
        )

    def check_operation_complete(self) -> int:
        """Gets the operation complete bit.
        Docs say this will always be 1 which is odd...

        Returns:
            int: Operation complete bit
        """

        return self.send_generic_command(
            self.cmds.GET_OPERATION_COMPLETE_BIT
        )

    def get_standard_event_enable_register(self) -> StatusRegister:
        """Gets the standard event register value and converts it to a
        StatusRegister.

        Returns:
            StatusRegister: StatusRegister object which can be queried.
        """

        resp = self.send_generic_command(
            self.cmds.GET_STANDARD_EVENT_ENABLE_REGISTER
        )

        return StatusRegister(resp)

    def get_standard_event_enable_register_and_clear(self) -> StatusRegister:
        """Gets the standard event register value and converts it to a
        StatusRegister and clears the device Register.

        Returns:
            StatusRegister: StatusRegister object which can be queried.
        """

        resp = self.send_generic_command(
            self.cmds.GET_STANDARD_EVENT_ENABLE_REGISTER_AND_CLEAR
        )

        return StatusRegister(resp)

    def check_errors(self) -> str:
        """Checks for errors and return if present

        Returns:
            str: Error if present or OK
        """
        resp = self.send_generic_command(
            self.cmds.QUERY_AND_CLEAR_EXECUTION_ERROR_REGISTER
        )

        # No error
        if resp == 0:
            return "OK"

        # Special case cause errors 1-9 are all internal hardware errors
        if resp in range(1, 10):
            return PL_POWER_SUPPLY_ERRORS[-1]

        # No idea
        if resp not in PL_POWER_SUPPLY_ERRORS:
            return f"Unknown error: {resp}"

        # Valid error code
        return PL_POWER_SUPPLY_ERRORS[resp]

    # TODO::Add support for missing commands at later date

    # TODO::Implement
    def clear_errors(self):
        pass

    def get_status(self):
        pass

    def initialise_device(self):
        pass

    def is_idle(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass
