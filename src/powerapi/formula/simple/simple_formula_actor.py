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
from typing import Dict

from powerapi.formula.formula_actor import FormulaActor
from powerapi.formula.handlers import FormulaPoisonPillMessageHandler
from powerapi.formula.simple.simple_handlers import ReportHandler
from powerapi.handler import StartHandler
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.pusher import PusherActor
from powerapi.report import HWPCReport, PowerReport


class SimpleFormulaActor(FormulaActor):
    """
    A fake Formula that sends the received rapport without processing it
    """

    def __init__(self, name, pushers: Dict[str, PusherActor], level_logger=logging.WARNING, timeout=None):
        """
            Initialize a new Simple Formula actor.
        """
        FormulaActor.__init__(self, name, pushers, level_logger, timeout)

    def setup(self):
        """
        Initialize Handler
        """
        FormulaActor.setup(self)
        self.add_handler(PoisonPillMessage, FormulaPoisonPillMessageHandler(self.state))
        self.add_handler(HWPCReport, ReportHandler(self.state))
        self.add_handler(PowerReport, ReportHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))
