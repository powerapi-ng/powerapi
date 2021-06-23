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

from thespian.actors import Actor, ActorSystem, ActorExitRequest

from powerapi.message import PingMessage, StartMessage, OKMessage
from powerapi.report import *


class DummyActor(Actor):
    """
    Actor that forward all received message to the actor system
    each message is wraped into a tuple that contains the actor name and the forwarded message
    the actor must be initialized by the actor system by sending its name (str) This message must be the first message that the dummy actor receive.
    It will not be forwarded

    """
    def __init__(self):
        Actor.__init__(self)
        self.name = None
        self.system_address = None

    def receiveMessage(self, message, sender):
        if self.name is None:
            self.name = message
            self.system_address = sender
        else:
            self.send(self.system_address, (self.name, message))


class DummyFormulaStartMessage(StartMessage):
    def __init__(self, name, puller_address):
        StartMessage.__init__(self, name)
        self.puller_address = puller_address


class DummyFormulaActor(Actor):
    """
    Formula that forward received message
    """
    def __init__(self):
        self.name = None
        self.fake_puller = None

    def receiveMessage(self, message, sender):
        if isinstance(message, StartMessage):
            self.name = message.name
            self.fake_puller = self.createActor(DummyActor, globalName=message.puller_address)
        if isinstance(message, ActorExitRequest):
            self.send(self.fake_puller, 'dead')
        else:
            self.send(self.fake_puller, message)


class CrashException(Exception):
    pass


class CrashFormulaActor(DummyFormulaActor):
    """
    Formula that crash after receiveing 3 messages
    """
    def __init__(self):
        DummyFormulaActor.__init__(self)
        self.report_received = 0

    def receiveMessage(self, message, sender):
        DummyFormulaActor.receiveMessage(self, message, sender)
        self.report_received += 1
        print(self.report_received)
        if self.report_received >= 3:
            self.send(self.fake_puller, 'crash')
            raise CrashException


def is_actor_alive(system, actor_address, time=1):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    msg = system.ask(actor_address, PingMessage(), time)
    print(msg)
    return isinstance(msg, OKMessage)

###################
# Report Creation #
###################
TS1 = 0
SENSOR1= 'sensor1'
TARGET1 = 'target1'
def gen_power_report():
    return PowerReport(TS1, SENSOR1, TARGET1, 0, 1234, {}, core=0)

def gen_hwpc_report():
    """
    Return a well formated HWPCReport
    """
    cpua = create_core_report('1', 'e0', '0')
    cpub = create_core_report('2', 'e0', '1')
    cpuc = create_core_report('1', 'e0', '2')
    cpud = create_core_report('2', 'e0', '3')
    cpue = create_core_report('1', 'ne1', '0')
    cpuf = create_core_report('2', 'e1', '1')
    cpug = create_core_report('1', 'e1', '2')
    cpuh = create_core_report('2', 'e1', '3')

    socketa = create_socket_report('1', [cpua, cpub])
    socketb = create_socket_report('2', [cpuc, cpud])
    socketc = create_socket_report('1', [cpue, cpuf])
    socketd = create_socket_report('2', [cpug, cpuh])

    groupa = create_group_report('1', [socketa, socketb])
    groupb = create_group_report('2', [socketc, socketd])

    return create_report_root([groupa, groupb])
