"""
PoisonPillMessageHandler class
"""
from smartwatts.handler import AbstractHandler
from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage


class PoisonPillMessageHandler(AbstractHandler):
    """ Generic handler for PoisonPillMessage
    """

    def handle(self, msg, state):
        """ Set the alive bool to False
        """
        if not isinstance(msg, PoisonPillMessage):
            raise UnknowMessageTypeException(type(msg))

        state.alive = False
        return state
