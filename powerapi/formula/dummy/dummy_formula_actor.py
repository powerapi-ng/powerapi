"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
import re
from functools import reduce

from powerapi.formula import FormulaActor, FormulaState
from powerapi.message import PoisonPillMessage
from powerapi.report import Report
from powerapi.handler import PoisonPillMessageHandler
from powerapi.formula.dummy.dummy_handlers import ReportHandler


class DummyFormulaActor(FormulaActor):
    """
    A fake Formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """
    def __init__(self, name, pushers, level_logger=logging.WARNING, timeout=None):
        """
        Initialize a new Dummy Formula actor.
        :param name: Actor name
        :param pusher_actors: Pusher actors
        :param level_logger: Level of the logger
        :param timeout: Time in millisecond to wait for a message before calling the timeout handler
        """
        FormulaActor.__init__(self, name, pushers, level_logger, timeout)

        #: (powerapi.State): Basic state of the Formula.
        self.state = FormulaState(self, pushers)

    def setup(self):
        """
        Initialize Handler
        """
        FormulaActor.setup(self)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(Report, ReportHandler(self.state))
