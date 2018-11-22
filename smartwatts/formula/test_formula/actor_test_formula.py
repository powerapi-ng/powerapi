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
