"""
Module actors
"""

import os
import multiprocessing
import pickle
import zmq


class Actor(multiprocessing.Process):
    """
    Abstract class of Actor.
    An actor is a process.
    """

    def __init__(self, context, name, cmd_socket_address, verbose=False):
        """
        Initialization and start of the process.

        Parameters:
            context(zmq.Context): context of the processus that create
            the actor
            cmd_socket_address(str)
        """
        multiprocessing.Process.__init__(self, name=name)
        self.verbose = verbose
        self.alive = True

        # If we consider this actor as a server, this context is used to
        # produce socket to communicate from the client
        self.context = context
        self.poller = None
        self.sockets = {}
        self.cmd_socket_address = cmd_socket_address

        self.cmd_socket = context.socket(zmq.PAIR)
        self.cmd_socket.connect(cmd_socket_address)

        # self.start()

    def log(self, message):
        """
        Print message if verbose mode is enable.
        """
        if self.verbose:
            print('['+str(os.getpid())+']' + ' ' + message)

    def add_socket(self, socket, name, address, poll_flag, connect_mode):
        """
        connect the actor to a socket and add this socket to the socket
        dictionary and the actor's poller

        params:
            socket(zmq.Socket)
            name(str): name of the socket, used as a key in the socket
                       dictionary
            address(str): socket address
            connect_mode(boolean): True to connect to socket, False to bind to
                                   socket
        """
        self.sockets[name] = socket
        self.poller.register(self.sockets[name], poll_flag)
        if connect_mode:
            self.sockets[name].connect(address)
        else:
            self.sockets[name].bind(address)

    def run(self):
        """
        code executed by the actor
        """

        # Basic initialization for ZMQ.
        self.context = zmq.Context()
        self.poller = zmq.Poller()

        # create the command socket (a pair socket used to communicate
        # with
        self.add_socket(self.context.socket(zmq.PAIR), 'cmd_socket',
                        self.cmd_socket_address, zmq.POLLIN, False)

        self.log('I\'m ' + self.name)
        self.log("running on address " + self.cmd_socket_address)

        # Define actor specific socket
        self.init_actor()

        # Run loop
        while self.alive:
            self.behaviour()

        self.terminated_behaviour()

    def terminated_behaviour(self):
        """
        function called before killing the actor
        """
        self.log("terminated")

    def behaviour(self):
        """
        Need to be overrided.
        Define the behaviour of the actor.
        """
        raise NotImplementedError

    def init_actor(self):
        """
        Need to be overrided.
        Function run before entering the run loop
        """
        raise NotImplementedError

    def send_serialized(self, socket, msg):
        """
        Allow to send a serialized msg with pickle
        """
        socket.send(pickle.dumps(msg))
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def recv_serialized(self, socket):
        """
        Allow to recv a serialized msg with pickle
        """
        msg = pickle.loads(socket.recv())
        self.log('received : ' + str(msg))
        return msg
