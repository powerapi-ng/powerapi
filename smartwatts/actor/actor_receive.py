"""
Module class ActorReceive
"""

import zmq
from smartwatts.actor.actor import Actor
from smartwatts.message import TermMessage, TERM


class ActorReceive(Actor):
    """
    Abstract class ActorReceive
    This type of actor do something only
    when it receive a new message.
    """

    def __init__(self, context, name, socket_address, verbose=False):
        Actor.__init__(self, context, name, socket_address, verbose)

    def handle_message(self, msg):
        """
        Behaviour when actor receive a new message.
        return True if the message was handled False otherwise
        """
        if msg.message_type == TERM:
            self.alive = False
            return True
        return False

    def behaviour(self):
        """
        wait for a message and handle it with the handle_message function
        """
        poll = self.poller.poll()
        active_sockets = [socket for (socket, event) in poll
                          if event == zmq.POLLIN]

        for socket in active_sockets:
            msg = self.recv_serialized(socket)

            self.handle_message(msg)

    def kill(self):
        self.send_serialized(self.cmd_socket, TermMessage())

    def send_cmd_msg(self, msg):
        """ send a message on the command socket """
        self.send_serialized(self.cmd_socket, msg)
