# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

    def _process_report(self, report):
        """
        Handle the RAPL events counter contained in a HWPC report.

        :param report: HWPC report to process
        :return: List of power report for each socket and RAPL event
        """

        if 'rapl' not in report.groups:
            return []

        reports = []
        for socket, socket_report in report.groups['rapl'].items():
            cores = list(socket_report.cores.values())
            for events_counter in cores:
                for event, counter in events_counter.events.items():
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

        result = self._process_report(msg)
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
