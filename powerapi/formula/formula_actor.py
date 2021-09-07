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
from typing import Dict, Type, Tuple

from thespian.actors import ActorAddress, ActorExitRequest

from powerapi.actor import Actor
from powerapi.message import FormulaStartMessage, EndMessage


class FormulaValues:
    """
    values used to initialize formula actor
    """
    def __init__(self, pushers: Dict[str, ActorAddress]):
        self.pushers = pushers


class DomainValues:
    """
    values that describe the device that the formula compute the power consumption for
    """
    def __init__(self, device_id: str, formula_id: Tuple):
        self.device_id = device_id
        self.sensor = formula_id[0]


class FormulaActor(Actor):
    """
    Abstract actor class used to implement formula actor that compute power consumption of a device from Reports
    """
    def __init__(self, start_message_cls: Type[FormulaStartMessage]):
        Actor.__init__(self, start_message_cls)
        self.pushers: Dict[str, ActorAddress] = None
        self.device_id = None
        self.sensor = None

    def _initialization(self, start_message: FormulaStartMessage):
        Actor._initialization(self, start_message)
        self.pushers = start_message.values.pushers
        self.device_id = start_message.domain_values.device_id
        self.sensor = start_message.domain_values.sensor

    def receiveMsg_EndMessage(self, message: EndMessage, _: ActorAddress):
        """
        when receiving a EndMessage kill itself
        """
        self.log_debug('received message ' + str(message))
        self.send(self.myAddress, ActorExitRequest())

    @staticmethod
    def gen_domain_values(device_id: str, formula_id: Tuple) -> DomainValues:
        """
        generate domain values of the formula from device and formula id
        """
        return DomainValues(device_id, formula_id)
