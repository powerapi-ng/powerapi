# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from __future__ import annotations
from typing import Type, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from powerapi.database import BaseDB
    from powerapi.filter import Filter
    from powerapi.dispatcher import RouteTable
    from powerapi.formula import FormulaActor, FormulaValues, DomainValues
    from powerapi.report_modifier import ReportModifier


class Message:
    """
    Abstract Message class
    """

    def __init__(self, sender_name: str):
        self.sender_name = sender_name

    def __str__(self):
        raise NotImplementedError()


class PingMessage(Message):
    """
    Message used to test if an actor is alive
    """

    def __init__(self, sender_name: str):
        Message.__init__(self, sender_name)

    def __str__(self):
        return "PingMessage"


class OKMessage(Message):
    """
    Message send to acknowledge last received message
    """

    def __init__(self, sender_name: str):
        Message.__init__(self, sender_name)

    def __str__(self):
        return "OKMessage"


class ErrorMessage(Message):
    """
    Message used to indicate that an error as occuried
    """

    def __init__(self, sender_name: str, error_message: str):
        """
        :param str error_code: message associated to the error
        """
        Message.__init__(self, sender_name)
        self.error_message = error_message

    def __str__(self):
        return "ErrorMessage : " + self.error_message


class StartMessage(Message):
    """
    Message that ask the actor to launch its initialisation process
    """

    def __init__(self, sender_name: str, name: str):
        Message.__init__(self, sender_name)
        self.name = name

    def __str__(self):
        return "StartMessage"


class EndMessage(Message):
    """
    Message sent by actor to its parent when it terminate itself
    """

    def __init__(self, sender_name: str):
        Message.__init__(self, sender_name)

    def __str__(self):
        return "EndMessage"


class PullerStartMessage(StartMessage):
    """
    Message used to start a Puller actor
    """

    def __init__(self, sender_name: str, name: str, database: BaseDB, report_filter: Filter, stream_mode: bool,
                 report_modifiers: List[ReportModifier] = []):
        """
        :param sender_name: name of the actor that send the message
        :param name: puller actor name
        :param database: database used by the puller to pull report
        :param report_filter: report filter used to filter reports
        :param stream_mode: True if stream mode is enabled
        :param report_modifier_list: list of ReportModifier used to modify report before sending them to dispatcher
        """
        StartMessage.__init__(self, sender_name, name)
        self.database = database
        self.report_filter = report_filter
        self.stream_mode = stream_mode
        self.report_modifier_list = report_modifiers


class SimplePullerStartMessage(StartMessage):
    """
    Message used to start a Puller actor
    """

    def __init__(self, sender_name: str, name: str, number_of_reports_to_send: int, report_filter: Filter,
                 report_type_to_send):
        """
            :param sender_name: name of the actor that send the message
            :param name: puller actor name
            :param number_of_reports_to_send: Number of messages to be sent by the actor
            :param report_type_to_send: Type of message to be sent
            :param report_filter:
        """
        StartMessage.__init__(self, sender_name, name)
        self.number_of_reports_to_send = number_of_reports_to_send
        self.report_type_to_send = report_type_to_send
        self.report_filter = report_filter


class DispatcherStartMessage(StartMessage):
    """
    Message used to start Dispatcher actor
    """

    def __init__(self, sender_name: str, name: str, formula_class: Type[FormulaActor], formula_values: FormulaValues,
                 route_table: RouteTable, device_id: str):
        """
        :param sender_name: name of the actor that send the message
        :param name: puller actor name
        :param formula_class: Class of the formula the dispatcher handle
        :param formula_values: Values that will be always passed to formula for initialization
        :param route_table: Dispatcher's Route table
        :param device_id: name of the device the dispatcher handle
        """
        StartMessage.__init__(self, sender_name, name)
        self.formula_class = formula_class
        self.formula_values = formula_values
        self.route_table = route_table
        self.device_id = device_id


class FormulaStartMessage(StartMessage):
    """
    Message used to start formula actor
    """

    def __init__(self, sender_name: str, name: str, formula_values: FormulaValues, domain_values: DomainValues):
        """
        :param sender_name: name of the actor that send the message
        :param name: puller actor name
        :param formula_values: values used by formula for initialization (depend of the formula class)
        :param domain_values: domain of the formula (depend of the formula class)
        """
        StartMessage.__init__(self, sender_name, name)
        self.values = formula_values
        self.domain_values = domain_values


class PusherStartMessage(StartMessage):
    """
    Message used to start a Pusher actor
    """

    def __init__(self, sender_name: str, name: str, database: BaseDB):
        """
        :param sender_name: name of the actor that send the message
        :param name: puller actor name
        :param BaseDB database: Database use for saving data.
        """
        StartMessage.__init__(self, sender_name, name)
        self.database = database


class SimplePusherStartMessage(StartMessage):
    """
    Message used to start a Simple Pusher actor
    """

    def __init__(self, sender_name: str, name: str):
        """
        :param sender_name: name of the actor that send the message
        :param name: simple puller actor name
        """
        StartMessage.__init__(self, sender_name, name)


class SimplePullerSendReportsMessage(Message):
    """
    Message used to trigger sending of message by a Simple Puller actor
    """

    def __init__(self, sender_name: str, name: str):
        """
            :param sender_name: name of the actor that send the message
            :param name: puller actor name
        """
        Message.__init__(self, sender_name)
        self.name = name

    def __str__(self):
        return "SimplePullerSendReportsMessage"


class GetReceivedReportsSimplePusherMessage(Message):
    """
    Message used to get the received reports of a simple pusher
    """

    def __init__(self, sender_name: str):
        """
        :param str error_code: message associated to the error
        """
        Message.__init__(self, sender_name)

    def __str__(self):
        return "GetReceivedReportsSimplePusherMessage : " + self.sender_name


class ReceivedReportsSimplePusherMessage(Message):
    """
    Message used to send reports of a simple pusher
    """

    def __init__(self, sender_name: str, reports:[]):
        """
        :param str error_code: message associated to the error
        """
        Message.__init__(self, sender_name)
        self.reports = reports

    def __str__(self):
        return "ReceivedReportsSimplePusherMessage : " + self.reports