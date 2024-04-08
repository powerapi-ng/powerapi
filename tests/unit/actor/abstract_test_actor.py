# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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
from multiprocessing import Pipe

import pytest
from mock import Mock

from powerapi.actor import Actor, NotConnectedException
from powerapi.handler import Handler
from powerapi.message import PoisonPillMessage, StartMessage, OKMessage, ErrorMessage
from powerapi.pusher import PusherActor
from powerapi.report import PowerReport, HWPCReport
from tests.utils.actor.dummy_actor import DummyActor
from tests.utils.db import SilentFakeDB

SENDER_NAME = 'test case'
PUSHER_NAME = 'test_pusher'


class FakeActor(Actor):

    def __init__(self, name, *args, queue=None, **kwargs):
        super().__init__(name)
        self.q = queue
        self.logger = Mock()
        self.logger.info = Mock()
        self.socket_interface = Mock()
        self.q.put((name, args, kwargs))
        self.alive = False

    def connect_data(self):
        pass

    def connect_control(self):
        pass

    def join(self, **kwargs):
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


def define_database_content(content):
    """
    Decorator used to define database content when using an actor with database

    ! If you use this decorator, you need to insert handler in  pytest_generate_tests function !
    ! see tests/unit/test_puller.py::pytest_generate_tests for example  !
    """

    def wrap(func):
        setattr(func, '_content', content)
        return func

    return wrap


def pytest_generate_tests_abstract(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the content fixtures in test environment with collected the
    value _content if it exists or with an empty content

    :param metafunc: the test context given by pytest
    """
    if 'content' in metafunc.fixturenames:
        content = getattr(metafunc.function, '_content', None)
        if isinstance(content, list):
            metafunc.parametrize('content', [content])
        else:
            metafunc.parametrize('content', [[]])


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
    actor.send_control(PoisonPillMessage(sender_name='system-test'))
    if actor.is_alive():
        actor.terminate()
    actor.socket_interface.close()

    join_actor(actor)


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
    actor.join()


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
TARGET_ACTOR_NAME = 'fake_target_actor'

REPORT_TYPE_TO_BE_SENT = PowerReport
REPORT_TYPE_TO_BE_SENT_2 = HWPCReport


def join_actor(actor):
    actor.join(timeout=10)


class AbstractTestActor:

    @staticmethod
    @pytest.fixture
    def pipe():
        return Pipe()

    @staticmethod
    @pytest.fixture
    def dummy_pipe_in(pipe):
        return pipe[0]

    @staticmethod
    @pytest.fixture
    def dummy_pipe_out(pipe):
        return pipe[1]

    @pytest.fixture
    def actor(self, request):
        """
        This fixture must return the actor class of the tested actor
        """
        raise NotImplementedError()

    @pytest.fixture
    def report_to_be_sent(self):
        """
        This fixture must return the report class for testing
        """
        raise NotImplementedError()

    @staticmethod
    @pytest.fixture
    def init_actor(actor):
        actor.start()
        actor.connect_data()
        actor.connect_control()
        yield actor

        if actor.is_alive():
            actor.terminate()
        actor.socket_interface.close()

        join_actor(actor)

    @staticmethod
    @pytest.fixture
    def started_actor(init_actor):
        init_actor.send_control(StartMessage('test_case'))
        _ = init_actor.receive_control(2000)
        yield init_actor

        init_actor.send_control(PoisonPillMessage())

    @staticmethod
    @pytest.fixture
    def started_fake_pusher_power_report(dummy_pipe_in):
        pusher = DummyActor(PUSHER_NAME_POWER_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT)
        start_actor(pusher)
        yield pusher
        if pusher.is_alive():
            pusher.terminate()

        join_actor(pusher)

    @staticmethod
    @pytest.fixture
    def started_fake_target_actor(report_to_be_sent, dummy_pipe_in):
        """
        Return a started DummyActor. When the test is finished, the actor is stopped
        """
        target_actor = DummyActor(name=TARGET_ACTOR_NAME, pipe=dummy_pipe_in, message_type=report_to_be_sent)
        target_actor.start()

        yield target_actor
        if target_actor.is_alive():
            target_actor.terminate()

    @staticmethod
    @pytest.fixture
    def started_fake_pusher_hwpc_report(dummy_pipe_in):
        pusher = DummyActor(PUSHER_NAME_HWPC_REPORT, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT_2)
        start_actor(pusher)
        yield pusher
        if pusher.is_alive():
            pusher.terminate()

        join_actor(pusher)

    @staticmethod
    @pytest.fixture
    def fake_pushers(started_fake_pusher_power_report, started_fake_pusher_hwpc_report):
        return {PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report, PUSHER_NAME_HWPC_REPORT: started_fake_pusher_hwpc_report}

    @staticmethod
    @pytest.fixture
    def actor_with_crash_handler(actor):
        actor.add_handler(CrashMessage, CrashHandler(actor.state))
        actor.add_handler(PingMessage, PingHandler(actor.state))

        actor.start()
        actor.connect_data()
        actor.connect_control()

        yield actor

        if actor.is_alive():
            actor.terminate()
        actor.socket_interface.close()

        join_actor(actor)

    @staticmethod
    @pytest.fixture
    def started_actor_with_crash_handler(actor_with_crash_handler):
        actor_with_crash_handler.send_control(StartMessage(SENDER_NAME))
        _ = actor_with_crash_handler.receive_control(2000)
        return actor_with_crash_handler

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_new_actor_is_alive(init_actor):
        assert init_actor.is_alive()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_PoisonPillMessage_set_actor_alive_to_False(init_actor):
        init_actor.send_control(PoisonPillMessage(sender_name='system-abstract-test'))
        time.sleep(0.1)
        assert not init_actor.is_alive()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_StartMessage_answer_OkMessage(init_actor):
        init_actor.send_control(StartMessage(SENDER_NAME))
        msg = init_actor.receive_control(2000)
        print('message start', str(msg))
        assert isinstance(msg, OKMessage)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(started_actor):
        started_actor.send_control(StartMessage(SENDER_NAME))
        msg = started_actor.receive_control(2000)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_message_on_data_canal_to_non_initialized_actor_raise_NotConnectedException(actor):
        with pytest.raises(NotConnectedException):
            actor.send_data(StartMessage(SENDER_NAME))

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_message_on_control_canal_to_non_initialized_actor_raise_NotConnectedException(actor):
        with pytest.raises(NotConnectedException):
            actor.send_control(StartMessage(SENDER_NAME))

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_low_exception_the_actor_must_stay_alive(actor_with_crash_handler):
        if not actor_with_crash_handler.low_exception:
            assert True
        else:
            exception = actor_with_crash_handler.low_exception[0]
            actor_with_crash_handler.send_data(CrashMessage(exception))
            assert is_actor_alive(actor_with_crash_handler, time=1)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_low_exception_the_actor_must_answer_to_ping_message(actor_with_crash_handler):
        actor_with_crash_handler.send_data(PingMessage())

        answer = actor_with_crash_handler.receive_control(2000)
        assert answer == 'pong'

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_fatal_exception_the_actor_must_be_killed(actor_with_crash_handler):
        actor_with_crash_handler.send_data(CrashMessage(TypeError()))
        assert not is_actor_alive(actor_with_crash_handler, time=1)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_starting_actor_with_a_no_StartMessage_does_no_change_initialized(init_actor):
        init_actor.send_control(ErrorMessage('system', 'error test'))
        assert not init_actor.state.initialized


class AbstractTestActorWithDB:

    @staticmethod
    @pytest.fixture
    def fake_db(content):
        return SilentFakeDB(content)

    @pytest.fixture
    def actor_with_db(self, fake_db, delay, buffer_size):
        raise NotImplementedError()

    @staticmethod
    @pytest.fixture
    def init_actor_with_db_and_crash_handler(actor_with_db):
        actor_with_db.state.add_handler(CrashMessage, CrashHandler(actor_with_db.state))
        actor_with_db.state.add_handler(PingMessage, PingHandler(actor_with_db.state))

        actor_with_db.start()
        actor_with_db.connect_data()
        actor_with_db.connect_control()

        yield actor_with_db

        if actor_with_db.is_alive():
            actor_with_db.terminate()
        actor_with_db.socket_interface.close()

        join_actor(actor_with_db)

    @staticmethod
    @pytest.fixture
    def init_actor_with_db(actor_with_db):
        actor_with_db.start()
        actor_with_db.connect_data()
        actor_with_db.connect_control()
        yield actor_with_db

        if actor_with_db.is_alive():
            actor_with_db.terminate()
        actor_with_db.socket_interface.close()

        join_actor(actor_with_db)

    @staticmethod
    @pytest.fixture
    def started_actor_with_db(init_actor_with_db, fake_db):
        init_actor_with_db.send_control(StartMessage('test_case'))
        _ = init_actor_with_db.receive_control(2000)
        yield init_actor_with_db

        init_actor_with_db.send_control(PoisonPillMessage())

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def started_actor_with_crash_handler(actor_with_db_and_crash_handler):
        actor_with_db_and_crash_handler.send_control(StartMessage(SENDER_NAME))
        _ = actor_with_db_and_crash_handler.receive_control(2000)
        return actor_with_db_and_crash_handler

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_new_actor_is_alive(init_actor_with_db):
        assert init_actor_with_db.is_alive()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_PoisonPillMessage_set_actor_alive_to_False(init_actor_with_db):
        init_actor_with_db.send_control(PoisonPillMessage(sender_name='system-abstract-test'))
        time.sleep(0.1)
        assert not init_actor_with_db.is_alive()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_StartMessage_answer_OkMessage(init_actor_with_db):
        init_actor_with_db.send_control(StartMessage(SENDER_NAME))
        msg = init_actor_with_db.receive_control(2000)
        print('message start', str(msg))
        assert isinstance(msg, OKMessage)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(started_actor_with_db):
        started_actor_with_db.send_control(StartMessage(SENDER_NAME))
        msg = started_actor_with_db.receive_control(2000)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_message_on_data_canal_to_non_initialized_actor_raise_NotConnectedException(actor_with_db):
        with pytest.raises(NotConnectedException):
            actor_with_db.send_data(StartMessage(SENDER_NAME))

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_message_on_control_canal_to_non_initialized_actor_raise_NotConnectedException(actor_with_db):
        with pytest.raises(NotConnectedException):
            actor_with_db.send_control(StartMessage(SENDER_NAME))

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_low_exception_the_actor_must_stay_alive(init_actor_with_db_and_crash_handler):
        if not init_actor_with_db_and_crash_handler.low_exception:
            assert True
        else:
            exception = init_actor_with_db_and_crash_handler.low_exception[0]
            init_actor_with_db_and_crash_handler.send_data(CrashMessage(exception))
            assert is_actor_alive(init_actor_with_db_and_crash_handler, time=1)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_low_exception_the_actor_must_answer_to_ping_message(init_actor_with_db_and_crash_handler):
        init_actor_with_db_and_crash_handler.send_data(PingMessage())

        answer = init_actor_with_db_and_crash_handler.receive_control(2000)
        assert answer == 'pong'

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_if_actor_behaviour_raise_fatal_exception_the_actor_must_be_killed(init_actor_with_db_and_crash_handler):
        init_actor_with_db_and_crash_handler.send_data(CrashMessage(TypeError()))
        assert not is_actor_alive(init_actor_with_db_and_crash_handler, time=1)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_starting_actor_with_a_no_StartMessage_does_no_change_initialized(init_actor_with_db):
        init_actor_with_db.send_control(ErrorMessage('system', 'error test'))
        assert not init_actor_with_db.state.initialized
