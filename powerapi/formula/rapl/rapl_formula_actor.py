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
import math
from powerapi.formula.formula_actor import FormulaActor
from powerapi.handler import Handler, PoisonPillMessageHandler
from powerapi.message import UnknowMessageTypeException, PoisonPillMessage
from powerapi.report import HWPCReport, PowerReport


class RAPLFormulaHWPCReportHandler(Handler):
    """
    This formula convert RAPL events counter value contained in a HWPC report
    to power reports.
    """

    def __init__(self, actor_pusher):
        self.actor_pusher = actor_pusher

    @staticmethod
    def _gen_power_report(report, socket, event, counter):
        """
        Generate a power report for a RAPL event.

        :param report: HWPC report
        :param socket: Socket ID
        :param event: RAPL event name
        :param counter: RAPL event counter
        """
        power = math.ldexp(counter, -32)
        metadata = {'socket': socket, 'event': event}
        return PowerReport(report.timestamp, report.sensor, report.target,
                           power, metadata)

    def _process_report(self, report, state):
        """
        Handle the RAPL events counter contained in a HWPC report.

        :param report: HWPC report to process
        :return: List of power report for each socket and RAPL event
        """

        if 'rapl' not in report.groups:
            return []

        reports = []
        for socket, socket_report in report.groups['rapl'].items():
            if len(state.formula_id) < 3 or int(state.formula_id[2]) == int(socket):
                for events_counter in socket_report.values():
                    for event, counter in events_counter.items():
                        if event.startswith('RAPL_'):
                            reports.append(self._gen_power_report(report, socket,
                                                                  event, counter))
        return reports

    def handle(self, msg, state):
        """
        Process a report and send the result(s) to a pusher actor.

        :param msg: Received message
        :param state: Current actor state
        :return: New actor state
        :raises UnknowMessageTypeException: if the given message is not an HWPCReport
        """
        if not isinstance(msg, HWPCReport):
            raise UnknowMessageTypeException(type(msg))

        result = self._process_report(msg, state)
        for report in result:
            self.actor_pusher.send_data(report)

        return state


class RAPLFormulaActor(FormulaActor):
    """
    A formula to handle RAPL events.
    """

    def __init__(self, name, actor_pusher, level_logger=logging.WARNING,
                 timeout=None):
        """
        Initialize an RAPL formula.
        :param name: Name of the formula
        :param actor_pusher: Pusher to whom the formula must send its reports
        :param int level_logger: Define the level of the logger
        """
        FormulaActor.__init__(self, name, actor_pusher, level_logger, timeout)

    def setup(self):
        """
        Setup the RAPL formula.
        """
        FormulaActor.setup(self)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        handler = RAPLFormulaHWPCReportHandler(self.actor_pusher)
        self.add_handler(HWPCReport, handler)
