""" Class that generalize formula behaviour """

from smartwatts.actor import Actor
from smartwatts.report import PowerReport


class AbstractActorFormula(Actor):
    """
    Generalize formula behaviour
    """

    def __init__(self, name, actor_pusher, verbose=False, timeout=None):
        """
        Parameters:
            @pusher(smartwatts.pusher.ActorPusher): Pusher to whom this formula
                                                    must send its reports
        """
        Actor.__init__(self, name, verbose)
        self.actor_pusher = actor_pusher

    def setup(self):
        """ Connect to actor pusher """
        self.actor_pusher.connect(self.context)

    def _post_handle(self, result):
        """ send computed estimation to the pusher

        Parameters:
            result(smartwatts.report.PowerReport)
        """
        if result is not None and isinstance(result, PowerReport):

            self.actor_pusher.send(result)
        else:
            return
