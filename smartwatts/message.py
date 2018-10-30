"""
Module message
"""

from enum import Enum


class _MessageType(Enum):
    TERM = 1
    HWPC_REPORT = 2
    POWERSPY_REPORT = 3
    ESTIMATION = 4


TERM = _MessageType.TERM
HWPC_REPORT = _MessageType.HWPC_REPORT
POWERSPY_REPORT = _MessageType.POWERSPY_REPORT
ESTIMATION = _MessageType.ESTIMATION


class Message:
    """
    Message that encapsulate data
    data type is given with the attribute message_type
    """

    def __init__(self, message_type, data):
        self.message_type = message_type
        self.data = data


class TermMessage(Message):
    def __init__(self):
        Message.__init__(self, TERM, -1)


class HWPCReportMessage(Message):
    def __init__(self, report):
        Message.__init__(self, HWPC_REPORT, report)


class PowerspyReportMessage(Message):
    def __init__(self, report):
        Message.__init__(self, POWERSPY_REPORT, report)


class EstimationMessage(Message):
    def __init__(self, report):
        Message.__init__(self, ESTIMATION, report)
