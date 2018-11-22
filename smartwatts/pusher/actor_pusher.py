"""
Module class ActorPusher
"""

from smartwatts.actor import Actor, Handler
from smartwatts.report import PowerReport


class _PowerHandler(Handler):
    """
    HWPCHandler class
    """

    def __init__(self, database):
        self.database = database
        self.database.load()

    def handle(self, msg):
        """
        Override

        Save the msg in the database
        """
        self.database.save(msg)


class ActorPusher(Actor):
    """ ActorPusher class """

    def __init__(self, name, report_type, database, verbose=False):
        Actor.__init__(self, name, verbose)
        self.report_type = report_type
        self.database = database

    def setup(self):
        """
        Override

        Specify for each kind of report the associate handler
        """
        self.handlers.append((PowerReport, _PowerHandler(self.database)))

    def post_handle(self):
        """
        Override
        """
        pass
