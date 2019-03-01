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

import pickle
import csv
import zmq


def is_actor_alive(actor):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    actor.join(0.5)
    return actor.is_alive()

#######################
# Function to log
#######################


def gen_side_effect(filename, msg):
    """
    generate a function for patching mocked methods with a side effect

    the side effect send a message to a given socket

    :param str filename: filename
    :param str msg: message to send to the socket
    """
    def log_side_effect(*args, **kwargs):
        with open(filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerows([[msg]])
            f.close()

    return log_side_effect


def is_log_ok(filename, validation_msg_list):
    """
    check if some side effects defined by gen_side_effect was apply

    :param str filename: file name for log
    :param list validation_msg_list: list of message that the side effects must
                                     send
    """

    """
    result_list = []
    for _ in range(len(validation_msg_list)):
        event = socket.poll(500)
        if event == 0:
            return False
        msg = pickle.loads(socket.recv())
        result_list.append(msg)

    result_list.sort()
    validation_msg_list.sort()

    return result_list == validation_msg_list
    """
    reader = csv.reader(filename)
    result_list = []
    for result in reader:
        result_list.append(result[0])

    result_list.sort()
    validation_msg_list.sort()
    return result_list == validation_msg_list

#######################
# Function to send data
#######################


def gen_send_side_effect(address):
    """
    Generate a function for patching mocked methods like send_data/send_monitor
    usually used for sending some data.

    :param Message msg: Msg to send
    """
    def send_side_effect(msg):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect(address)
        socket.send(pickle.dumps(msg))
        socket.close()
        context.destroy()

    return send_side_effect


def receive_side_effect(address, context):
    """
    Return Message send by the gen_send_side_effect.

    :param str address: Address of the socket where the side effect must send
                        the message
    :param zmq.context context: Zmq context used for receiving message from the
                                side effect
    :rtype boolean: True if all the waited message was received,
                    False otherwise
    """
    socket = context.socket(zmq.PULL)
    socket.bind(address)

    result_list = []
    while True:
        event = socket.poll(500)
        if event == 0:
            break
        msg = pickle.loads(socket.recv())
        result_list.append(msg)
    socket.close()

    return result_list
