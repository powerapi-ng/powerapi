"""
Module actor_puller
"""

from smartwatts.actor import Actor


class ActorPuller(Actor):
    """ ActorPuller class """

    def __init__(self, name, database, filt, timeout, verbose=False):
        """
        Initialization

        Parameters:
            @database: BaseDB object
            @filter: Filter object
        """
        Actor.__init__(self, name, verbose, timeout=timeout)
        self.database = database
        self.filter = filt

    def init_actor(self):
        """
        Override

        Connect to all dispatcher in filter and load the db
        """
        for _, dispatcher in self.filter.filters:
            dispatcher.connect(self.context)

        self.database.load()

    def initial_receive(self, msg):
        """
        Override
        """
        return

    def behaviour(self):
        """
        Override

        This actor read each report in db and simply filter it
        in his filter, then send it (or not) to the dispatcher.
        """
        # Read one input
        report = self.database.get_next()

        # Filter the report
        dispatcher = self.filter.route(report)

        # Send to the dispatcher if it's not None
        if dispatcher is not None:
            dispatcher.send(report)
