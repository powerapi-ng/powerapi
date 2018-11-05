"""
Module class ActorReporter
"""

from smartwatts.actor.actor_pull import PullActor
from smartwatts.message import ESTIMATION
import smartwatts.config as config


def gen_reporter(context, verbose=False):
    """ Factory function for generate Reporter """
    reporter = ActorReporterStdOut(context, 'reporter',
                                   config.REPORTER_SOCKET_ADDRESS,
                                   config.REPORTER_PULL_SOCKET_ADDRESS,
                                   verbose=verbose)
    reporter.start()
    return reporter


class ActorReporter(PullActor):
    """ StdOutActorReporter class """

    def __init__(self, context, name, socket_address, pull_socket_address,
                 verbose=False):
        PullActor.__init__(self, context, name, socket_address,
                           pull_socket_address, verbose=verbose)

    def output(self, msg):
        """ Display msg['values'] """
        self.log(msg['values'])

    def handle_message(self, msg):
        if PullActor.handle_message(self, msg):
            return True
        if msg.message_type == ESTIMATION:
            self.output(msg.data)
            return True
        return False
