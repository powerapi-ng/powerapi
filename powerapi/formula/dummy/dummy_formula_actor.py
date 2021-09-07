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
import time
from typing import Dict

from thespian.actors import ActorAddress

from powerapi.formula import AbstractCpuDramFormula, FormulaValues
from powerapi.report import Report, PowerReport
from powerapi.message import FormulaStartMessage


class DummyFormulaValues(FormulaValues):
    """
    Formula values with configurable sleeping time for dummy formula
    """
    def __init__(self, pushers: Dict[str, ActorAddress], sleeping_time: int):
        FormulaValues.__init__(self, pushers)
        self.sleeping_time = sleeping_time


class DummyFormulaActor(AbstractCpuDramFormula):
    """
    A fake Formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """
    def __init__(self):
        """
        Initialize a new Dummy Formula actor.
        :param name: Actor name
        :param pusher_actors: Pusher actors
        """
        AbstractCpuDramFormula.__init__(self, FormulaStartMessage)

        self.sleeping_time = None

    def _initialization(self, message: FormulaStartMessage):
        AbstractCpuDramFormula._initialization(self, message)
        self.sleeping_time = message.values.sleeping_time

    def receiveMsg_Report(self, message: Report, _: ActorAddress):
        """
        When receiving a report sleep for a given time and produce a power report with a power consumption of 42W
        """
        self.log_debug('received message ' + str(message))
        time.sleep(self.sleeping_time)
        power_report = PowerReport(message.timestamp, message.sensor, message.target, 42, {'socket': self.socket})
        for _, pusher in self.pushers.items():
            self.send(pusher, power_report)
