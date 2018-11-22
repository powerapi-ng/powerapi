""" Handler interface """


class Handler:
    """ Handler interface """
    def handle(self, msg):
        """ Handle a message and return a value

        Parameters:
            msg(Object): the message received by the actor

        Return:
            (Object): computation on the message result
        """
        raise NotImplementedError
