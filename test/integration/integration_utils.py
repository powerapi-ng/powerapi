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
function used to communicate with mocked actors
"""

def gen_side_effect(address, msg):
    """
    generate a function for patching mocked methods with a side effect

    the side effect send a message to a given socket

    :param str address: address of the socket
    :msg str socket: message to send to the socket
    """
    def log_side_effect(*args, **kwargs):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect(address)
        socket.send(pickle.dumps(msg))
        socket.close()

    return log_side_effect


def is_log_ok(address, validation_msg_list, context):
    """
    check if some side effects defined by gen_side_effect was apply

    :param str address: address of the socket where the side effect must send
                        the message
    :param list validation_msg_list: list of message that the side effects must
                                     send
    :param zmq.context context: zmq context used for receiving message from the
                                side effect
    :rtype boolean: True if all the waited message was received, False otherwise
    """
    socket = context.socket(zmq.PULL)
    socket.bind(address)

    result_list = []
    for _ in range(len(validation_msg_list)):
        event = socket.poll(500)
        if event == 0:
            return False
        msg = pickle.loads(socket.recv())
        result_list.append(msg)
    socket.close()

    result_list.sort()
    validation_msg_list.sort()

    return result_list == validation_msg_list
