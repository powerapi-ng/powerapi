"""
Module class ActorPusher
"""

from smartwatts.message import UnknowMessageTypeException
from smartwatts.actor import Actor


class ActorPusher(Actor):
    """ ActorPusher class """

    def __init__(self, name, report_type, database, verbose=False):
        Actor.__init__(self, name, verbose)
        self.report_type = report_type
        self.database = database

    def init_actor(self):
        """
        Override
        """
        pass

    def initial_receive(self, msg):
        """
        Override
        """
        if isinstance(msg, self.report_type):
            self.database.save(msg)
        else:
            raise UnknowMessageTypeException

    def behaviour(self):
        """
        Override
        """
        pass
