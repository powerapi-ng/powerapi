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
import time
from powerapi.formula.formula_actor import FormulaActor
from powerapi.message import UnknowMessageTypeException, PoisonPillMessage
from powerapi.report import Report, PowerReport
from powerapi.handler import Handler, PoisonPillMessageHandler


class DummyHWPCReportHandler(Handler):
    """
    A fake handler that simulate data processing
    """

    def __init__(self, actor_pusher):
        self.actor_pusher = actor_pusher

    def _process_report(self, report):
        """
        Wait 1 second and return a power report containing 42

        :param powerapi.Report report: Received report

        :return: A power report containing consumption estimation
        :rtype:  powerapi.PowerReport
        """

        result_msg = PowerReport(report.timestamp, report.sensor,
                                 report.target, {}, 42)
        return result_msg

    def handle(self, msg, state):
        """
        Process a report and send the result to the pusher actor

        :param powerapi.Report msg:       Received message
        :param powerapi.State state: Actor state

        :return: New Actor state
        :rtype:  powerapi.State

        :raises UnknowMessageTypeException: If the msg is not a Report
        """
        if not isinstance(msg, Report):
            raise UnknowMessageTypeException(type(msg))

        result = self._process_report(msg)
        self.actor_pusher.send_data(result)
        return state


class DummyFormulaActor(FormulaActor):
    """
    A fake Formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """

    def __init__(self, name, actor_pusher, level_logger=logging.WARNING,
                 timeout=None):
        """
        :param str name:                            Actor name
        :param powerapi.PusherActor actor_pusher: Pusher to send results.
        """
        FormulaActor.__init__(self, name, actor_pusher, level_logger, timeout)

    def setup(self):
        """
        Initialize Handler
        """
        FormulaActor.setup(self)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        handler = DummyHWPCReportHandler(self.actor_pusher)
        self.add_handler(Report, handler)
