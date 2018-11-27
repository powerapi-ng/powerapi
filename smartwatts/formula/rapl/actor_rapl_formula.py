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
from smartwatts.actor import Handler


def _gen_power_report(base_report, socket_id, rapl_event_id, power):
    metadata = {'socket': socket_id, 'rapl_event_id': rapl_event_id}
    return PowerReport(base_report.timestamp, base_report.sensor,
                       base_report.target, power, metadata)


class RAPLFormulaHWPCReportHandler(Handler):
    """
    A test formula that simulate data processing
    """

    def handle(self, msg):
        """ Extract RAPL reports from a HWPC report and convert their values in
        Joules

        Return:
            ([smartwatts.report.PowerReport]): a power report per RAPL report

        Raise:
            UnknowMessageTypeException: if the *msg* is not a HWPCReport
        """
        if not isinstance(msg, HWPCReport):
            raise UnknowMessageTypeException

        if 'rapl' not in msg.groups:
            return []

        reports = []
        for socket_id, socket_report in msg.groups['rapl']:
            core_report = socket_report.cores.values()[0]
            for event_id, raw_power in core_report.events.items():
                power = math.ldexp(raw_power, -32)
                reports.append(_gen_power_report(msg, socket_id, event_id,
                                                 power))
        return reports


class RAPLFormula(FormulaActor):
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
        FormulaActor.__init__(self, name, verbose)
        self.actor_pusher = actor_pusher

    def setup(self):
        """ Initialize Handler """
        self.actor_pusher.connect(self.context)
        self.handlers.append(HWPCReport, RAPLFormulaHWPCReportHandler)

    def _post_handle(self, result):
        """ send computed estimation to the pusher

        Parameters:
            result([smartwatts.report.PowerReport])
        """
        for report in result:
            self.actor_pusher.send(report)
