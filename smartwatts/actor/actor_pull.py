"""
An actor that can receive messages from multiple sources using a push/pull
socket
"""

import zmq
from smartwatts.actor.actor_receive import ActorReceive


class PullActor(ActorReceive):
    """ PullActor class """

    def __init__(self, context, name, cmd_socket_address, pull_socket_address,
                 verbose=False):

        ActorReceive.__init__(self, context, name, cmd_socket_address,
                              verbose=verbose)
        self.push_socket = None
        self.pull_socket_address = pull_socket_address

    def send(self, msg):
        """ Send msg by push_socket """
        self.send_serialized(self.push_socket, msg)

    def send_json(self, msg):
        """ Send json msg to the actor """
        self.push_socket.send_json(msg)
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def connect(self):
        """
        initialize the push/pull connection with the actor
        """
        # define the push_socket on the client side
        self.push_socket = self.context.socket(zmq.PUSH)
        # connect to the pull socket on the server_side
        self.push_socket.connect(self.pull_socket_address)
        self.log('connected to ' + self.pull_socket_address)

    def init_actor(self):
        """
        Define the push/pull socket
        """
        self.add_socket(self.context.socket(zmq.PULL), 'pull_socket',
                        self.pull_socket_address, zmq.POLLIN, False)
        self.log('bound to ' + self.pull_socket_address)
