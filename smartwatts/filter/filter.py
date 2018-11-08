"""
Module filter
"""


class Filter:
    """ Filter abstract class """

    def __init__(self):
        self.filters = []

    def get_type(self):
        """
        Need to be overrided.

        Return the report type for a filter.
        """
        raise NotImplementedError

    def filter(self, rule, dispatcher):
        """
        Define a rule for a new report, and send it to the dispatcher
        if the rule accept it.

        Parameters:
            @rule: function which return true of false
            @dispatcher: Actor we want to send the report
        """
        self.filters.append((rule, dispatcher))

    def route(self, msg):
        """
        Return the dispatcher to whom
        send the msg, or None

        Parameters:
            @msg: msg to send
        """
        for rule, dispatcher in self.filters:
            if rule(msg):
                return dispatcher

        return None
