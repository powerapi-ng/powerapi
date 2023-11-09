# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from powerapi.database import BaseDB
    from powerapi.filter import Filter
    from powerapi.dispatcher import RouteTable
    from powerapi.formula import FormulaActor, FormulaState


class Message:
    """
    Abstract Message class
    """

    def __init__(self, sender_name: str):
        self.sender_name = sender_name

    def __str__(self):
        raise NotImplementedError()


class OKMessage(Message):
    """
    Message sends to acknowledge last received message
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
    Message that asks the actor to launch its initialisation process
    """

    def __init__(self, sender_name: str):
        Message.__init__(self, sender_name)

    def __str__(self):
        return "StartMessage"


class EndMessage(Message):
    """
    Message sent by actor to its parent when it terminates itself
    """

    def __init__(self, sender_name: str):
        Message.__init__(self, sender_name)

    def __str__(self):
        return "EndMessage"


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

    def __init__(self, sender_name: str, reports: []):
        """
        :param str sender_name: name of the message sender
        :param list reports: list of stored reports
        """
        Message.__init__(self, sender_name)
        self.reports = reports

    def __str__(self):
        return "ReceivedReportsSimplePusherMessage : " + str(self.reports)


class PoisonPillMessage(Message):
    """
    Message which allow to kill an actor
    """

    def __init__(self, soft: bool = True, sender_name: str = ''):
        Message.__init__(self, sender_name=sender_name)
        self.is_soft = soft
        self.is_hard = not soft

    def __str__(self):
        return "PoisonPillMessage"

    def __eq__(self, other):
        if isinstance(other, PoisonPillMessage):
            return other.is_soft == self.is_soft and other.is_hard == self.is_hard
        return False
