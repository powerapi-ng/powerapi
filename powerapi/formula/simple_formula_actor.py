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
import time
from typing import Dict

from thespian.actors import ActorAddress

from powerapi.formula import AbstractCpuDramFormula, FormulaValues, FormulaActor
from powerapi.report import Report, PowerReport
from powerapi.message import FormulaStartMessage


class SimpleFormulaActor(FormulaActor):
    """
    A fake Formula that sends the received rapport without processing it
    """

    def __init__(self):
        """
        Initialize a new Simple Formula actor.
        :param name: Actor name
        :param pusher_actors: Pusher actors
        """
        FormulaActor.__init__(self, FormulaStartMessage)

    def _initialization(self, message: FormulaStartMessage):
        FormulaActor._initialization(self, message)

    def receiveMsg_Report(self, message: Report, _: ActorAddress):
        """
        When receiving a report send it to the destinations
        """
        self.log_debug('received message ' + str(message))

        for _, pusher in self.pushers.items():
            self.send(pusher, message)
