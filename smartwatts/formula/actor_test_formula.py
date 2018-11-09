"""
Module ActorTestFormula
"""

import time

from smartwatts.actor.basic_messages import UnknowMessageTypeException
from smartwatts.actor import Actor
from smartwatts.report import HWPCReport, PowerReport


class ActorTestFormula(Actor):
    """
    A test formula that simulate data processing by waiting 1s and send a
    power report containing 42

    """
    def __init__(self, name, reporter, verbose=False):
        """
        Parameters:
            reporter(smartwatts.reporter.Reporter): Reporter that this formula
                                                    must send its reports
        """
        Actor.__init__(self, name, verbose)

        self.reporter = reporter

    def init_actor(self):
        """
        connect to the reporter actor
        """
        self.reporter.connect(self.context)

    def initial_receive(self, msg):
        if isinstance(msg, HWPCReport):
            time.sleep(1)
            msg = PowerReport(42)
            self.reporter.send(msg)
        else:
            raise UnknowMessageTypeException(type(msg))

    def behaviour(self):
        return
