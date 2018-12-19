"""
Handlers used by PullerActor
"""

from smartwatts.handler import AbstractInitHandler, AbstractHandler
from smartwatts.database import DBErrorException
from smartwatts.message import ErrorMessage, OKMessage, StartMessage


class NoReportExtractedException(Exception):
    """ Exception raised when the handler can't extract a report from the given
    database

    """
    pass


class StartHandler(AbstractHandler):

    """ Handle Start Message

    launch database interface
    """
    def __init__(self, next_behaviour):
        self.next_behaviour = next_behaviour

    def handle(self, msg, state):
        """ Initialize the database and connect all dispatcher to the
        socket_interface
        """
        if state.initialized:
            return state

        if not isinstance(msg, StartMessage):
            return state

        try:
            state.database.load()
        except DBErrorException as error:
            state.socket_interface.send_monitor(ErrorMessage(error.msg))
            return state

        # Connect to all dispatcher
        for _, dispatcher in state.report_filter.filters:
            dispatcher.connect(state.socket_interface.context)

        state.initialized = True
        state.socket_interface.send_monitor(OKMessage())
        state.behaviour = self.next_behaviour
        return state
