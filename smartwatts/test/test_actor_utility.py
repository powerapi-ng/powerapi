# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Class and function to test actors
"""

import pickle
import zmq


class MessageInterceptor:
    """
    class used to intercept message sent by tested actors
    """
    def __init__(self, context):
        self.context = context
        self.pull_socket_address = 'ipc://@msg_interceptor'

        self.pull_socket = self.context.socket(zmq.PULL)
        self.pull_socket.bind(self.pull_socket_address)

        self.push_socket = None

    def connect(self, context):
        """
        Connect to the pull socket

        open a push socket on the process that want to communicate with the
        message interceptor

        parameters:
            context(zmq.Context): ZMQ context of the process that want to
                                  communicate with the message interceptor
        """
        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(self.pull_socket_address)

    def send(self, msg):
        """
        Send a msg to the message interceptor

        This function will not be used by the message interceptor but by process
        that want to send message to the message interceptor
        """
        self.push_socket.send(pickle.dumps(msg))

    def receive(self, timeout):
        """
        wait for a message for a given time
        if no message was received during the given time, return None

        Parameters:
            timeout(int): timeout in millisecond
        Return(Message | None): the received message or None if no message was
                                received during the given time
        """
        if not self.pull_socket.poll(timeout):
            return None
        return pickle.loads(self.pull_socket.recv())
