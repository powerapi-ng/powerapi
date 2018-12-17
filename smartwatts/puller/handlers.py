"""
Handlers used by PullerActor
"""
from smartwatts.handler import AbstractInitHandler, AbstractHandler
from smartwatts.database import DBErrorException
from smartwatts.message import ErrorMessage, OKMessage


class NoReportExtractedException(Exception):
    """ Exception raised when the handler can't extract a report from the given
    database

    """
    pass


class StartHandler(AbstractHandler):

    """ Handle Start Message

    launch database interface
    """

    def handle(self, msg, state):
        """ Initialize the database and connect all dispatcher to the
        socket_interface
        """
        if state.initialized:
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
        return state


class TimeoutHandler(AbstractInitHandler):
    """
    TimeoutHandler class
    """

    def __init__(self, autokill=False):
        self.autokill = autokill

    def _get_report_dispatcher(self, state):
        """
        read one report of the database and filter it,
        then return the tuple (report, dispatcher).

        Return:
            (Report, DispatcherActor): (extracted_report, dispatcher to sent
                                        this report)

        Raise:
            NoReportExtractedException : if the database doesn't contains
                                         report anymore

        """
        # Read one input, if it's None, it means there is not more
        # report in the database, just pass
        json = state.database.get_next()
        if json is None:
            raise NoReportExtractedException()

        # Deserialization
        report = state.report_filter.get_type()()
        report.deserialize(json)

        # Filter the report
        dispatcher = state.report_filter.route(report)
        return (report, dispatcher)

    def handle(self, msg, state):
        """
        Handle the send of the report to the good dispatcher
        """
        try:
            (report, dispatcher) = self._get_report_dispatcher(state)

        except NoReportExtractedException:
            if self.autokill:
                state.alive = False
            return state

        # Send to the dispatcher if it's not None
        if dispatcher is not None:
            dispatcher.send(report)

        return state
