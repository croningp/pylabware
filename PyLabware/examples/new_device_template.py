"""PyLabware driver for NEW_DEVICE."""

# You may want to import serial if the device is using serial connection and any
# connection options (baudrate/parity/...) need to be changed
# import serial

# You would need appropriate abstract types from typing
from typing import Optional, Union

# Core imports
from .. import parsers as parser
from ..controllers import APPROPRIATE_ABSTRACT_DEVICE, in_simulation_device_returns

# You would typically need at minimum SLConnectionError to handle broken
# connection exceptions properly in is_connected()/is_idle()
# from ..exceptions import SLConnectionError

from ..models import LabDeviceCommands, ConnectionParameters


class NEW_DEVICECommands(LabDeviceCommands):
    """Collection of command definitions for for NEW_DEVICE. These commands are
    based on the <language> section of the manufacturers user manual,
    version <version>, pages <pages>.
    """

    # ##########################  Constants ##################################
    # Add any relevant constants/literals - e.g device id, name - to this
    # section.
    NEW_DEVICE_NAME = "MY_AWESOME_DEVICE"

    # ################### Control commands ###################################
    # Add command dealing with device control/operation to this section.
    # An example of command with no reply and arguments
    BLINK_SCREEN = {"name": "BS"}

    # An example of command with no reply and a single int argument
    SET_TEMP = {"name": "ST", "type": int}

    # An example of command with no reply and a single int argument with value checking
    SET_TEMP_WITH_CHECK = {"name": "ST", "type": int, "check": {"min": 20, "max": 300}}

    # An example of command with no reply and a single str argument with value checking
    SET_ROTATION_DIR = {"name": "SRD", "type": str, "check": {"values": ["cw", "ccw", "CW", "CCW"]}}

    # An example of command with no arguments and an integer reply that has to
    # be cut out from reply string at positions 2-5
    GET_TEMP = {"name": "GT", "reply": {"type": str, "parser": parser.slicer, "args": [2, 5]}}

    # ################### Configuration commands #############################
    # Add commands altering device configuration/settings to this section.


class NEW_DEVICE(APPROPRIATE_ABSTRACT_DEVICE):
    """
    This provides a Python class for the IKA RCT Digital hotplate
    based on the english section of the original
    operation manual 201811_IKAPlate-Lab_A1_25002139a.
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int], auto_connect: bool):
        """Default constructor
        """

        # Load commands from helper class
        self.cmd = NEW_DEVICECommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        # Change any connection settings to device specific ones, if needed
        # connection_parameters["port"] = port
        # connection_parameters["address"] = address
        # connection_parameters["baudrate"] = 9600
        # connection_parameters["bytesize"] = serial.SEVENBITS
        # connection_parameters["parity"] = serial.PARITY_EVEN

        super().__init__(device_name, connection_mode, connection_parameters, auto_connect)

        # Protocol settings
        # Terminator for the command string (from host to device)
        self.command_terminator = "\r\n"
        # Terminator for the reply string (from device to host)
        self.reply_terminator = "\r\n"
        # Separator between command and command arguments, if any
        self.args_delimiter = " "

    def initialise_device(self):
        """Set default operation mode & reset.
        """

    # Wrapping is_connected is an easy way to ensure correct behavior in
    # simulation. See respective documentation section for the detailed explanation.
    @in_simulation_device_returns(NEW_DEVICECommands.NEW_DEVICE_NAME)
    def is_connected(self) -> bool:
        """"""

    def is_idle(self) -> bool:
        """"""

    def get_status(self):
        """"""

    def check_errors(self):
        """"""

    def clear_errors(self):
        """"""
