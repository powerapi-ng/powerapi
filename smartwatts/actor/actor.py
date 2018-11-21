"""
Module actors
"""

import os
import multiprocessing
import pickle
import zmq

from smartwatts.actor.basic_messages import PoisonPill
from smartwatts.message import UnknowMessageTypeException

class Actor(multiprocessing.Process):
    """
    Abstract class of Actor.
    An actor is a process.
    """

    def __init__(self, name, verbose=False, timeout=None):
        """
        Initialization and start of the process.

        Parameters:
            @name(str): unique name that will be used to indentify the actor
                        communication socket
            @verbose(bool): allow to display log
            @timeout(int): if define, do something if no msg is recv every
                           timeout
        """
        multiprocessing.Process.__init__(self, name=name)

        # Value used
        # This socket is used to connect to the pull socket of this actor. It
        # won't be created on the actor's process but on the process that want
        # to connect to the pull socket of this actor
        self.push_socket = None

        self.verbose = verbose
        self.alive = True
        self.context = None
        self.pull_socket_address = 'ipc://@' + self.name
        self.pull_socket = None
        self.timeout = timeout

        self.timeout_handler = None
        self.handlers = []
        
    def log(self, message):
        """
        Print message if verbose mode is enable.
        """
        if self.verbose:
            print('['+str(os.getpid())+']' + ' ' + message)

    def run(self):
        """
        code executed by the actor
        """

        # Basic initialization for ZMQ.
        self.context = zmq.Context()

        # create the pull socket (to comunicate with this actor, others process
        # have to connect a push socket to this socket)
        self.pull_socket = self.context.socket(zmq.PULL)
        self.pull_socket.bind(self.pull_socket_address)

        self.log('I\'m ' + self.name)
        self.log("running on address " + self.pull_socket_address)

        # actors specific initialisation
        self.setup()

        # Run loop
        while self.alive:
            msg = self.__recv_serialized(self.pull_socket)

            # Timeout
            if msg is None:
                self.timeout_handler.handle(None)
            # Kill msg
            elif isinstance(msg, PoisonPill):
                self.alive = False
            else:
                for (msg_type, handler) in self.handlers:
                    if isinstance(msg, msg_type):
                        handler.handle(msg)
                        continue
                raise UnknowMessageTypeException

        self.terminated_behaviour()

    def setup(self):
        """
        Need to be overrided.

        Define actor specific processing that is run before entering the Run
        Loop
        """
        raise NotImplementedError

    def terminated_behaviour(self):
        """
        Can be overrided.

        function called before killing the actor
        """
        self.log("terminated")

    def __send_serialized(self, socket, msg):
        """
        Allow to send a serialized msg with pickle
        """
        socket.send(pickle.dumps(msg))
        self.log('sent ' + str(msg) + ' to ' + self.name)

    def __recv_serialized(self, socket):
        """
        Allow to recv a serialized msg with pickle
        """
        if not socket.poll(self.timeout):
            return None
        msg = pickle.loads(socket.recv())
        self.log('received : ' + str(msg))
        return msg

    def connect(self, context):
        """connect to the pull socket of this actor

        open a push socket on the process that want to communicate with this
        actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  communicate with this actor

        """
        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)
        self.log('connected to ' + self.pull_socket_address)

    def send(self, msg):
        """Send a msg to this actor

        This function will not be used by this actor but by process that
        want to send message to this actor
        """
        self.__send_serialized(self.push_socket, msg)

    def kill(self):
        """
        kill this actor by sending a PoisonPill message
        """
        self.send(PoisonPill())
