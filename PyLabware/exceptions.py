"""PyLabware  exceptions"""


class PLConnectionError(ConnectionError):
    """ Generic connection error, base class."""


class PLConnectionProtocolError(PLConnectionError):
    """Error in transport protocol."""


class PLConnectionTimeoutError(PLConnectionError):
    """Connection timeout error."""


class PLDeviceError(Exception):
    """Generic device error, base class."""


class PLDeviceCommandError(PLDeviceError):
    """Error in processing device command.

    This should be any error arising BEFORE the command has been sent to a device.
    """


class PLDeviceReplyError(PLDeviceError):
    """Error in processing device reply.

    This should be any error arising AFTER the command has been sent to the device.
    """


class PLDeviceInternalError(PLDeviceReplyError):
    """Error returned by device as a response to command.
    """
