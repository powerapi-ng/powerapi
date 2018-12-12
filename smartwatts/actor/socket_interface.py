""" class SocketInterface """

import zmq
import pickle


class SocketInterface:
    """ Class that group all method that handle sockets """

    def __init__(self, name, timeout):
        """
        Parameters:
            name(str): name of the actor using this interface
        """
        self.timeout = timeout
        self.pull_socket_address = 'ipc://@' + name
        self.monitor_socket_address = 'ipc://@monitor_' + name

        self.context = None
        self.poller = None

        self.pull_socket = None
        self.monitor_socket = None

        # This socket is used to connect to the pull socket of this actor. It
        # won't be created on the actor's process but on the process that want
        # to connect to the pull socket of this actor
        self.push_socket = None

    def setup(self):
        """ Initialize zmq context and sockets """
        # Basic initialization for ZMQ.
        self.context = zmq.Context()
        self.poller = zmq.Poller()

        # create the pull socket (to communicate with this actor, others
        # process have to connect a push socket to this socket)
        self.pull_socket = self._create_socket(zmq.PULL,
                                               self.pull_socket_address)

        # create the monitor socket (to monitor this actor, a process have to
        # connect a pair socket to this socket with the `monitor` method)
        self.monitor_socket = self._create_socket(zmq.PAIR,
                                                  self.monitor_socket_address)

    def _create_socket(self, socket_type, socket_addr):
        """create a socket of the given type, bind it to the given address and
        register it to the poller

        Return:
            (zmq.Socket): the initialized socket
        """
        socket = self.context.socket(socket_type)
        socket.bind(socket_addr)
        self.poller.register(socket, zmq.POLLIN)
        return socket

    def receive(self):
        """ Wait for messages and return them

        Return: a list of received messages since the last receive call
                or [] if timeout
        """
        events = self.poller.poll(self.timeout)

        return [self._recv_serialized(socket) for socket, event in events
                if event == zmq.POLLIN]

    def close(self):
        """ close socket interface

        close all socket handle by this interface
        """
        if self.pull_socket is not None:
            self.pull_socket.close()

        if self.monitor_socket is not None:
            self.monitor_socket.close()

    def _send_serialized(self, socket, msg):
        """
        Allow to send a serialized msg with pickle
        """
        socket.send(pickle.dumps(msg))

    def _recv_serialized(self, socket):
        """
        Allow to recv a serialized msg with pickle
        """
        msg = pickle.loads(socket.recv())
        return msg

    def connect(self, context):
        """
        Connect to the pull socket of this actor

        open a push socket on the process that want to communicate with this
        actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  communicate with this actor

        """
        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)

    def disconect(self):
        """
        close connection to the pull socket and monitor socket of this actor
        """
        if self.push_socket is not None:
            self.push_socket.close()

        if self.monitor_socket is not None:
            self.push_socket.close()

    def monitor(self, context):
        """
        Connect to the monitor socket of this actor

        open a pair socket on the process that want to monitor this actor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  monitor this actor

        """
        self.monitor_socket = context.socket(zmq.PAIR)
        self.monitor_socket.connect(self.monitor_socket_address)

    def send_monitor(self, msg):
        """ Send a message to this actor the monitor socket"""
        self._send_serialized(self.monitor_socket, msg)

    def send(self, msg):
        """ Send a message on the push socket"""
        self._send_serialized(self.push_socket, msg)
