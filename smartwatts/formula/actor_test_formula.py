"""
Module ActorTestFormula
"""

import time

from smartwatts.message import UnknowMessageTypeException
from smartwatts.actor import Actor
from smartwatts.report import HWPCReport, PowerReport


class ActorTestFormula(Actor):
    """
    ActorTestFormula class

    A test formula that simulate data processing by waiting 1s and send a
    power report containing 42
    """

    def __init__(self, name, pusher, verbose=False):
        """
        Parameters:
            @pusher(smartwatts.pusher.ActorPusher): Pusher to whom this formula
                                                    must send its reports
        """
        Actor.__init__(self, name, verbose)

        self.pusher = pusher

    def init_actor(self):
        """ Override """

        # Connect to the pusher actor
        self.pusher.connect(self.context)

    def initial_receive(self, msg):
        """ Override """
        if isinstance(msg, HWPCReport):
            time.sleep(1)
            msg = PowerReport(42)
            self.pusher.send(msg)
        else:
            raise UnknowMessageTypeException(type(msg))

    def behaviour(self):
        """ Override """
        return
