"""
PoisonPillMessageHandler class
"""
from smartwatts.handler import AbstractHandler
from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage


class PoisonPillMessageHandler(AbstractHandler):
    """ Generic handler for PoisonPillMessage
    """

    def handle(self, msg, state):
        """ Set the :attr:~smartwatts.actor.state.BasicState.alive attribute of
        the actor state to False

        :param Object msg: the message received by the actor
        :param state: The current actor's state
        :type state: smartwatts.actor.state.BasicState

        :return: The new actor's state
        :rtype: smartwatts.actor.state.BasicState
        """
        if not isinstance(msg, PoisonPillMessage):
            raise UnknowMessageTypeException(type(msg))

        state.alive = False
        return state
