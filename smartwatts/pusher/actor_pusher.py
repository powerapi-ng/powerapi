"""
Module class ActorPusher
"""

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
        return

    def initial_receive(self, msg):
        """
        Override
        """
        # TODO: Check if msg is report type
        self.database.save(msg)

    def behaviour(self):
        """
        Override
        """
        return
