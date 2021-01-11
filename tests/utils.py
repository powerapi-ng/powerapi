# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import multiprocessing
import os
import time
import pickle
import sys

import zmq

from powerapi.handler import Handler
from powerapi.report import PowerReport, Report
from powerapi.formula import FormulaActor, FormulaState, FormulaPoisonPillMessageHandler
from powerapi.message import PoisonPillMessage
from powerapi.actor import SafeContext


def is_actor_alive(actor, time=0.5):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    actor.join(time)
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
        socket = SafeContext.get_context().socket(zmq.PUSH)
        socket.connect(filename)
        socket.send_string(msg)
        socket.close()

    return log_side_effect


def is_log_ok(filename, validation_msg_list):
    """
    check if some side effects defined by gen_side_effect was apply

    :param str filename: file name for log
    :param list validation_msg_list: list of message that the side effects must
                                     send
    """

    result_list = []
    for _ in range(len(validation_msg_list)):
        event = filename.poll(500)
        if event == 0:
            return False
        msg = filename.recv_string()
        result_list.append(msg)

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


#################
# Crash Formula #
#################
class CrashState(FormulaState):
    def __init__(self, actor, pushers, metadata, nb_reports_max, exception):
        FormulaState.__init__(self, actor, pushers, metadata)
        self.nb_reports = 0
        self.nb_reports_max = nb_reports_max
        self.exception = exception

    def reinit(self):
        self.nb_reports = 0


class CrashException(Exception):
    pass


class ReportHandler(Handler):
    def _estimate(self, report):
        if self.state.nb_reports >= self.state.nb_reports_max:
            raise self.state.exception()

        self.state.nb_reports += 1
        metadata = {'formula_name': self.state.actor.name}

        socket_id = self.state.metadata['socket'] if 'socket' in self.state.metadata else -1

        result_msg = PowerReport(report.timestamp, report.sensor, report.target, socket_id, 42, metadata)
        return [result_msg]

    def handle(self, msg):
        results = self._estimate(msg)
        for _, actor_pusher in self.state.pushers.items():
            for result in results:
                actor_pusher.send_data(result)


class CrashFormulaActor(FormulaActor):
    def __init__(self, name, pushers, nb_reports_max, exception, level_logger=logging.WARNING, timeout=None):
        FormulaActor.__init__(self, name, pushers, level_logger, timeout)
        self.state = CrashState(self, pushers, self.formula_metadata, nb_reports_max, exception)
        self.low_exception = [CrashException]

    def setup(self):
        FormulaActor.setup(self)
        self.add_handler(PoisonPillMessage, FormulaPoisonPillMessageHandler(self.state))
        self.add_handler(Report, ReportHandler(self.state))
