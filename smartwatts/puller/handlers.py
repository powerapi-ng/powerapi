"""
Handlers used by PullerActor
"""
from smartwatts.handler import AbstractHandler


class NoReportExtractedException(Exception):
    """ Exception raised when the handler can't extract a report from the given
    database

    """
    pass


class TimeoutHandler(AbstractHandler):
    """
    TimeoutHandler class
    """

    def __init__(self, database, filt, autokill=False):
        self.database = database
        self.filter = filt
        self.database.load()
        self.autokill = autokill

    def _get_report_dispatcher(self):
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
        json = self.database.get_next()
        if json is None:
            raise NoReportExtractedException()

        # Deserialization
        report = self.filter.get_type()()
        report.deserialize(json)

        # Filter the report
        dispatcher = self.filter.route(report)
        return (report, dispatcher)

    def handle(self, msg, state):
        """
        Handle the send of the report to the good dispatcher
        """
        try:
            (report, dispatcher) = self._get_report_dispatcher()

        except NoReportExtractedException:
            if self.autokill:
                state.alive = False
            return state

        # Send to the dispatcher if it's not None
        if dispatcher is not None:
            dispatcher.send(report)

        return state
