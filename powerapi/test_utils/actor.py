# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import sys
from typing import Dict

import pytest

from powerapi.handler import PoisonPillMessageHandler
from powerapi.report import Report, PowerReport, HWPCReport
from powerapi.pusher import PusherActor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor
from powerapi.formula import FormulaActor
from powerapi.message import PusherStartMessage, PullerStartMessage, DispatcherStartMessage, FormulaStartMessage, \
    StartMessage, PoisonPillMessage
from powerapi.message import PingMessage, OKMessage

PUSHER_NAME = 'test_pusher'
PULLER_NAME = 'test_puller'
DISPATCHER_NAME = 'test_dispatcher'
DISPATCHER_DEVICE_ID = 'test_device'


class ActorLogFilter(logging.Filter):
    """
    Log filter
    """

    def filter(self, record):
        """
        filter logs that was produced by actor
        """
        return 'actor_name' in record.__dict__


class NotActorLogFilter(logging.Filter):
    """
    Log filter
    """

    def filter(self, record):
        """
        filter logs that was not produced by actor
        """
        return 'actorAddress' not in record.__dict__


LOG_DEF = {
    'version': 1,
    'formatters': {
        'normal': {'format': '%(levelname)s::%(created)s::ROOT::%(message)s'},
        'actor': {'format': '%(levelname)s::%(created)s::%(actor_name)s::%(message)s'}},
    'filters': {
        'isActorLog': {'()': ActorLogFilter},
        'notActorLog': {'()': NotActorLogFilter}},
    'handlers': {
        'h1': {'class': 'logging.StreamHandler',
               'stream': sys.stdout,
               'formatter': 'normal',
               'filters': ['notActorLog'],
               'level': logging.DEBUG},
        'h2': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'actor',
            'filters': ['isActorLog'],
            'level': logging.DEBUG}
    },
    'loggers': {'': {'handlers': ['h1', 'h2'], 'level': logging.DEBUG}}
}


@pytest.fixture()
def puller(database, report_filter, stream_mode):
    """
    fixture that create a PullerActor before launching the test and stop it after the test end
    """
    actor = PullerActor(name=PULLER_NAME, database=database, report_filter=report_filter, stream_mode=stream_mode,
                        report_model=HWPCReport)

    yield actor
    actor.send_control(PoisonPillMessage())


@pytest.fixture()
def puller_start_message(database, report_filter, stream_mode):
    return StartMessage("test case")


@pytest.fixture()
def started_puller(system, puller, puller_start_message):
    """
    fixture that create and start a PullerActor and actor before launching the test and stop it after the test end
    """
    puller.send_control(puller_start_message)
    return puller


@pytest.fixture()
def pusher(database):
    """
    fixture that create a PusherActor before launching the test and stop it after the test end
    """
    actor = PusherActor(name=PUSHER_NAME, database=database, report_model=PowerReport)

    actor.start()
    actor.connect_data()
    actor.connect_control()

    yield actor
    actor.send_control(PoisonPillMessage())
    if actor.is_alive():
        actor.terminate()
    actor.socket_interface.close()


@pytest.fixture()
def pusher_start_message():
    """
    return a pusher start message
    """
    return StartMessage("test case")


@pytest.fixture()
def started_pusher(system, pusher, pusher_start_message):
    """
    fixture that create and start a PusherActor and actor before launching the test and stop it after the test end
    """
    pusher.send_control(pusher_start_message)
    return pusher


@pytest.fixture()
def dispatcher(formula_class, route_table):
    """
    fixture that create a DispatcherActor before launching the test and stop it after the test end
    """
    actor = DispatcherActor(name= DISPATCHER_NAME, formula_init_function=formula_class.__init__, route_table=route_table)

    yield actor
    actor.send_control(PoisonPillMessage())


@pytest.fixture()
def dispatcher_start_message(formula_class, route_table):
    """
    return a dispatcher start message
    """
    return StartMessage('test case')


@pytest.fixture()
def started_dispatcher(system, dispatcher, dispatcher_start_message):
    """
    fixture that create and start a DispatcherActor and actor before launching the test and stop it after the test end
    """
    dispatcher.send_control(dispatcher_start_message)
    return dispatcher

# TODO IS IT REQUIRED ?
# class CrashFormula(FormulaActor):
#     """
#     Formula that crash when receiving a report
#     """
#
#     def __init__(self, name: str, pushers: Dict):
#         FormulaActor.__init__(self, name, pushers)
#
#     @staticmethod
#     def receiveMsg_Report(message: Report, sender: ActorAddress):
#         """
#         crash when receiving a report
#         """
#         raise Exception()


# def is_actor_alive(system, actor_address, time=1):
#     """
#     wait the actor to terminate or 0.5 secondes and return its is_alive value
#     """
#     msg = system.ask(actor_address, PingMessage('system'), time)
#     return isinstance(msg, OKMessage)
