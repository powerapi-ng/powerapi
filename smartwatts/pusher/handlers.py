"""
Handlers used by PusherActor
"""
from smartwatts.handler import AbstractInitHandler
from smartwatts.report import PowerReport
from smartwatts.message import UnknowMessageTypeException


class PowerHandler(AbstractInitHandler):
    """
    HWPCHandler class
    """

    def __init__(self, database):
        self.database = database
        self.database.load()

    def handle(self, msg, state):
        """
        Override

        Save the msg in the database
        """
        if not isinstance(msg, PowerReport):
            raise UnknowMessageTypeException

        self.database.save(msg.serialize())
        return state
