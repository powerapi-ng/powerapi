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

import logging
from typing import Any

from powerapi.actor import Actor
from powerapi.formula.abstract_cpu_dram_formula import AbstractCpuDramFormula, AbstractCpuDramFormulaState
from powerapi.formula.handlers import FormulaPoisonPillMessageHandler
from powerapi.handler import StartHandler
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.report import Report
from tests.utils.formula.dummy.dummy_handlers import ReportHandler


class DummyFormulaState(AbstractCpuDramFormulaState):
    """
    Formula values with configurable sleeping time for dummy formula
    """

    def __init__(self, actor: Actor, pushers: dict[str, Actor], metadata: dict[str, Any], socket: str, core: str,
                 sleep_time: int):
        AbstractCpuDramFormulaState.__init__(self, actor, pushers, metadata, socket, core)
        self.sleep_time = sleep_time


class DummyFormulaActor(AbstractCpuDramFormula):
    """
    A fake Formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """

    def __init__(self, name, pushers, socket, core, level_logger=logging.WARNING, sleep_time=0, timeout=None):
        """
        Initialize a new Dummy Formula actor.
        :param name: Actor name
        :param pushers: Pusher actors
        :param socket:
        :param core:
        :param level_logger: Level of the logger
        :param timeout: Time in millisecond to wait for a message before calling the timeout handler
        """
        AbstractCpuDramFormula.__init__(self, name, pushers, socket, core, level_logger, timeout)

        #: (powerapi.State): Basic state of the Formula.
        self.state = DummyFormulaState(self, pushers, self.formula_metadata, socket, core, sleep_time)

    def setup(self):
        """
        Initialize Handler
        """
        AbstractCpuDramFormula.setup(self)
        self.add_handler(PoisonPillMessage, FormulaPoisonPillMessageHandler(self.state))
        self.add_handler(Report, ReportHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))
