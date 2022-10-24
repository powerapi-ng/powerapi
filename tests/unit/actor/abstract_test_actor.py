# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
import time

from multiprocessing import Queue, Pipe
from mock import Mock

import pytest

from powerapi.message import PoisonPillMessage, StartMessage, OKMessage, ErrorMessage
from powerapi.actor import Actor, NotConnectedException
from powerapi.handler import Handler
from powerapi.report import PowerReport, HWPCReport
from powerapi.test_utils.db import FakeDB
from powerapi.test_utils.dummy_actor import DummyActor

SENDER_NAME = 'test case'


class FakeActor(Actor):

    def __init__(self, name, *args, queue=None, **kwargs):
        self.q = queue
        self.logger = Mock()
        self.logger.info = Mock()
        self.name = name
        self.socket_interface = Mock()
        self.q.put((name, args, kwargs))
        self.alive = False

    def connect_data(self):
        pass

    def connect_control(self):
        pass

    def join(self):
        pass

    def is_alive(self):
        return self.alive

    def hard_kill(self):
        self.alive = False
        self.q.put('hard kill')

    def soft_kill(self):
        self.alive = False
        self.q.put('soft kill')

    def send_data(self, msg):
        self.q.put(msg)

    def send_control(self, msg):
        self.q.put(msg)

    def start(self):
        self.alive = True
        self.q.put('start')

    def terminate(self):
        self.q.put('terminate')


def is_actor_alive(actor, time=0.5):
    """
    wait the actor to terminate or 0.5 secondes and return its is_alive value
    """
    actor.join(time)
    return actor.is_alive()


def recv_from_pipe(pipe, timeout):
    """
    add timeout to function pipe.recv
    """
    if pipe.poll(timeout):
        return pipe.recv()
    else:
        return None, None


def start_actor(actor: Actor):
    """
    Starts a given actor as a new process and initialises the related socket
    :param actor: Actor to be started
    """
    actor.start()
    actor.connect_control()
    actor.connect_data()
    actor.send_control(StartMessage('system'))
    _ = actor.receive_control(2000)


def stop_actor(actor: Actor):
    """
    Stops a given actor
    :param actor: Actor to be stopped
    """
    if actor.is_alive():
        actor.terminate()
    actor.socket_interface.close()


class CrashMessage:
    def __init__(self, exception_type):
        self.exception_type = exception_type


class PingMessage:
    pass


class PingHandler(Handler):
    def handle_message(self, msg):
        self.state.actor.send_control('pong')


class CrashHandler(Handler):

    def handle_message(self, msg: CrashMessage):
        raise msg.exception_type


PUSHER_NAME_POWER_REPORT = 'fake_pusher_power'
PUSHER_NAME_HWPC_REPORT = 'fake_pusher_hwpc'

REPORT_TYPE_TO_BE_SENT = PowerReport
REPORT_TYPE_TO_BE_SENT_2 = HWPCReport


class AbstractTestActor:

    @pytest.fixture
    def pipe(self):
        return Pipe()

    @pytest.fixture
    def dummy_pipe_in(self, pipe):
        return pipe[0]

    @pytest.fixture
    def dummy_pipe_out(self, pipe):
        return pipe[1]

    @pytest.fixture
    def actor(self):
        """
        This fixture must return the actor class of the tested actor
        """
        raise NotImplementedError()

    @pytest.fixture
    def init_actor(self, actor):
        actor.start()
        actor.connect_data()
        actor.connect_control()
        yield actor
        if actor.is_alive():
            actor.terminate()
        actor.socket_interface.close()

    @pytest.fixture
    def started_actor(self, init_actor):
        init_actor.send_control(StartMessage('test_case'))
        _ = init_actor.receive_control(2000)
        return init_actor

    @pytest.fixture
    def started_fake_pusher_power_report(self, dummy_pipe_in):
        pusher = DummyActor(PUSHER_NAME_POWER_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT)
        start_actor(pusher)
        yield pusher
        if pusher.is_alive():
            pusher.terminate()

    @pytest.fixture
    def started_fake_pusher_hwpc_report(self, dummy_pipe_in):
        pusher = DummyActor(PUSHER_NAME_HWPC_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT_2)
        start_actor(pusher)
        yield pusher
        if pusher.is_alive():
            pusher.terminate()

    @pytest.fixture
    def fake_pushers(self, started_fake_pusher_power_report, started_fake_pusher_hwpc_report):
        return {PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report,
                PUSHER_NAME_HWPC_REPORT: started_fake_pusher_hwpc_report}

    @pytest.fixture
    def actor_with_crash_handler(self, actor):
        actor.state.handlers = [
            (CrashMessage, CrashHandler(actor.state)),
            (PingMessage, PingHandler(actor.state))
        ]

        actor.start()
        actor.connect_data()
        actor.connect_control()

        yield actor

        if actor.is_alive():
            actor.terminate()
        actor.socket_interface.close()

    @pytest.fixture
    def started_actor_with_crash_handler(self, actor_with_crash_handler):
        actor_with_crash_handler.send_control(StartMessage(SENDER_NAME))
        _ = actor_with_crash_handler.receive_control(2000)
        return actor_with_crash_handler

    def test_new_actor_is_alive(self, init_actor):
        assert init_actor.is_alive()

    def test_send_PoisonPillMessage_set_actor_alive_to_False(self, init_actor):
        init_actor.send_control(PoisonPillMessage())
        time.sleep(0.1)
        assert not init_actor.is_alive()

    def test_send_StartMessage_answer_OkMessage(self, init_actor):
        init_actor.send_control(StartMessage(SENDER_NAME))
        msg = init_actor.receive_control(2000)
        print('Message....')
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(self, started_actor):
        started_actor.send_control(StartMessage(SENDER_NAME))
        msg = started_actor.receive_control(2000)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    def test_send_message_on_data_canal_to_non_initialized_actor_raise_NotConnectedException(self, actor):
        with pytest.raises(NotConnectedException):
            actor.send_data(StartMessage(SENDER_NAME))

    def test_send_message_on_control_canal_to_non_initialized_actor_raise_NotConnectedException(self, actor):
        with pytest.raises(NotConnectedException):
            actor.send_control(StartMessage(SENDER_NAME))

    def test_if_actor_behaviour_raise_low_exception_the_actor_must_stay_alive(self, actor_with_crash_handler):
        if actor_with_crash_handler.low_exception == []:
            assert True
        else:
            exception = actor_with_crash_handler.low_exception[0]
            actor_with_crash_handler.send_data(CrashMessage(exception))
            assert is_actor_alive(actor_with_crash_handler, time=1)

    def test_if_actor_behaviour_raise_low_exception_the_actor_must_answer_to_ping_message(self,
                                                                                          actor_with_crash_handler):
        actor_with_crash_handler.send_data(PingMessage())

        answer = actor_with_crash_handler.receive_control(2000)
        assert answer == 'pong'

    def test_if_actor_behaviour_raise_fatal_exception_the_actor_must_be_killed(self, actor_with_crash_handler):
        actor_with_crash_handler.send_data(CrashMessage(TypeError()))
        assert not is_actor_alive(actor_with_crash_handler, time=1)

    def test_starting_actor_with_a_no_StartMessage_does_no_change_initialized(self, init_actor):
        init_actor.send_control(ErrorMessage('system', 'error test'))
        assert not init_actor.state.initialized


class AbstractTestActorWithDB(AbstractTestActor):

    @pytest.fixture
    def fake_db(self, content):
        return FakeDB(content)

    @pytest.fixture
    def started_actor(self, init_actor, fake_db):
        init_actor.send_control(StartMessage(SENDER_NAME))
        # remove OkMessage from control socket
        _ = init_actor.receive_control(2000)
        # remove 'connected' string from Queue
        _ = fake_db.q.get(timeout=2)
        return init_actor

    def test_starting_actor_make_it_connect_to_database(self, init_actor, fake_db):
        init_actor.send_control(StartMessage(SENDER_NAME))
        assert fake_db.q.get(timeout=2) == 'connected'
