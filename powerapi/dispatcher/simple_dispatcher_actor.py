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
from typing import Type, Tuple, List

from thespian.actors import ActorAddress, ActorExitRequest, ChildActorExited, PoisonMessage

from powerapi.actor import Actor, InitializationException
from powerapi.formula import FormulaActor, FormulaValues
from powerapi.dispatch_rule import DispatchRule
from powerapi.utils import Tree
from powerapi.report import Report
from powerapi.message import StartMessage, DispatcherStartMessage, FormulaStartMessage, EndMessage, ErrorMessage, \
    OKMessage
from powerapi.dispatcher.blocking_detector import BlockingDetector
from powerapi.dispatcher.route_table import RouteTable


class SimpleDispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self):
        Actor.__init__(self, DispatcherStartMessage)
        
        self.formula_pool = {}
        self.formula_number_id = 0
        self.formula = None

    def _initialization(self, message: StartMessage):
        Actor._initialization(self, message)
        self.formula_class = message.formula_class
        self.formula_values = message.formula_values
        self.route_table = message.route_table
        self.device_id = message.device_id
        self.formula_name = "simple-formula"

        self._create_formula(("simple-formula", self.formula_class), self.formula_name)

    def _send_message(self, formula, message):
        self.log_debug('send ' + str(message) + ' to ' + self.formula_name)
        self.send(formula, message)

    def receiveMsg_Report(self, message: Report, _: ActorAddress):
        """
        When receiving a report, split it into sub-reports (if needed) and send them to their corresponding formula.
        If the corresponding formula does not exist, the dispatcher create it and send it the report
        """
        self.log_debug('received ' + str(message))
        self._send_message(self.formula, message)

    def receiveMsg_OKMessage(self, message: OKMessage, sender: ActorAddress):
        """
        When receiving OKMessage after trying to start a formula, move formula from the waiting service to the formula pool
        """
        formula_name = message.sender_name
        self.log_info('formula ' + formula_name + ' started')

    def _create_formula(self, formula_id: Tuple, formula_name: str):
        self.formula = self.createActor(self.formula_class)
        domain_values = self.formula_class.gen_domain_values(self.device_id, formula_id)
        start_message = FormulaStartMessage(self.name, formula_name, self.formula_values, domain_values)
        self.send(self.formula, start_message)
        self.log_info('create formula ' + formula_name)
