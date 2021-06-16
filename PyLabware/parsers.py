"""PyLabware utility functions for reply parsing"""

import re


def slicer(reply: str, *args) -> str:
    """This is a wrapper function for reply parsing to provide consistent
    arguments order.

    Args:
        reply: Sequence object to slice.

    Returns:
        (any): Slice of the original object.
    """

    return reply[slice(*args)]


def researcher(reply, *args):
    """This is a wrapper function for reply parsing to provide consistent
    arguments order.

    Args:
        reply: Reply to parse with regular expression.

    Returns:
        (re.Match): Regular expression match object.
    """

    return re.search(*args, reply)


def stripper(reply: str, prefix=None, suffix=None) -> str:
    """This is a helper function used to strip off reply prefix and
    terminator. Standard Python str.strip() doesn't work reliably because
    it operates on character-by-character basis, while prefix/terminator
    is usually a group of characters.

    Args:
        reply: String to be stripped.
        prefix: Substring to remove from the beginning of the line.
        suffix: Substring to remove from the end of the line.

    Returns:
        (str): Naked reply.
    """

    if prefix is not None and reply.startswith(prefix):
        reply = reply[len(prefix):]

    if suffix is not None and reply.endswith(suffix):
        reply = reply[:-len(suffix)]

    return reply
