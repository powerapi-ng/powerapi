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
import time
from smartwatts.formula import AbstractActorFormula
from smartwatts.message import UnknowMessageTypeException
from smartwatts.report import Report, PowerReport
from smartwatts.actor import Handler


class TestFormulaReportHandler(Handler):
    """
    A test formula that simulate data processing
    """

    def handle(self, msg):
        """ Wait 1 seconde and return a power report containg 42

        Return:
            (smartwatts.report.PowerReport): a power report containing
                                             comsumption estimation
        Raise:
            UnknowMessageTypeException: if the *msg* is not a Report
        """
        if isinstance(msg, Report):
            time.sleep(1)
            result_msg = PowerReport(42)
            return result_msg

        raise UnknowMessageTypeException(type(msg))


class ActorTestFormula(AbstractActorFormula):
    """
    ActorTestFormula class

    A test formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """

    def setup(self):
        """ Initialize Handler """
        AbstractActorFormula.setup(self)
        self.handlers.append(Report, TestFormulaReportHandler)
