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
import time
from smartwatts.formula.formula_actor import FormulaActor
from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage
from smartwatts.report import Report, PowerReport
from smartwatts.handler import Handler, PoisonPillMessageHandler


class DummyHWPCReportHandler(Handler):
    """
    A fake handler that simulate data processing
    """

    def __init__(self, actor_pusher):
        self.actor_pusher = actor_pusher

    def _process_report(self, report):
        """
        Wait 1 second and return a power report containing 42

        :param smartwatts.Report report: Received report

        :return: A power report containing consumption estimation
        :rtype:  smartwatts.PowerReport
        """

        time.sleep(1)
        result_msg = PowerReport(report.timestamp, report.sensor,
                                 report.target, {}, 42)
        return result_msg

    def handle(self, msg, state):
        """
        Process a report and send the result to the pusher actor

        :param smartwatts.Report msg:       Received message
        :param smartwatts.State state: Actor state

        :return: New Actor state
        :rtype:  smartwatts.State

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

    def __init__(self, name, actor_pusher, level_logger=logging.NOTSET,
                 timeout=None):
        """
        :param str name:                            Actor name
        :param smartwatts.PusherActor actor_pusher: Pusher to send results.
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
