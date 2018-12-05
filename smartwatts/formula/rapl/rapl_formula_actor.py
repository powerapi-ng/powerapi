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

"""
Module ActorTestFormula
"""
import math

from smartwatts.formula.formula_actor import FormulaActor
from smartwatts.message import UnknowMessageTypeException
from smartwatts.report import HWPCReport, PowerReport
from smartwatts.handler import AbstractHandler


def _gen_power_report(base_report, socket_id, rapl_event_id, power):
    metadata = {'socket': socket_id, 'event': rapl_event_id}
    return PowerReport(base_report.timestamp, base_report.sensor,
                       base_report.target, power, metadata)


class RAPLFormulaHWPCReportHandler(AbstractHandler):
    """
    A test formula that simulate data processing
    """

    def __init__(self, actor_pusher):
        self.actor_pusher = actor_pusher

    def _process_report(self, report):
        """ Extract RAPL reports from a HWPC report and convert their values in
        Joules

        Parameters:
            (smartwatts.report.HWPCReport): received hwpc report

        Return:
            ([smartwatts.report.PowerReport]): a power report per RAPL reports
                                               in the hwpc report

        """

        if 'rapl' not in report.groups:
            return []

        reports = []
        for socket_id, socket_report in report.groups['rapl'].items():
            core_report = list(socket_report.cores.values())[0]
            for event_id, raw_power in core_report.events.items():
                power = math.ldexp(raw_power, -32)
                reports.append(_gen_power_report(report, socket_id, event_id,
                                                 power))
        return reports

    def handle(self, msg, state):
        """ process a report and send the result to the pusher actor

        Parameters:
            msg(smartwatts.report.HWPCReport) : received message
            state(smartwatts.actor.BasicState) : current actor state

        Return:
            state(smartwatts.actor.BasicState): new actor state

        Raise:
            UnknowMessageTypeException: if the *msg* is not a Report
        """
        if not isinstance(msg, HWPCReport):
            raise UnknowMessageTypeException(type(msg))

        result = self._process_report(msg)
        for report in result:
            self.actor_pusher.send(report)

        return state


class RAPLFormulaActor(FormulaActor):
    """
    ActorTestFormula class

    A test formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """

    def __init__(self, name, actor_pusher, verbose=False):
        """
        Parameters:
            @pusher(smartwatts.pusher.ActorPusher): Pusher to whom this formula
                                                    must send its reports
        """
        FormulaActor.__init__(self, name, actor_pusher, verbose)

    def setup(self):
        """ Initialize Handler """
        FormulaActor.setup(self)
        self.handlers.append((HWPCReport,
                              RAPLFormulaHWPCReportHandler(self.actor_pusher)))
