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
from multiprocessing import Pipe

import pytest

from thespian.actors import ActorSystem

from powerapi.message import OKMessage, ErrorMessage, PingMessage, EndMessage

from .db import FakeDB, CrashDB
from .dummy_actor import DummyActor, DummyStartMessage, logger
from .actor import system, is_actor_alive

LOGGER_NAME = 'thespian_test_logger'


def recv_from_pipe(pipe, timeout):
    """
    add timeout to function pipe.recv
    """
    if pipe.poll(timeout):
        return pipe.recv()
    else:
        return None, None


class UnknowMessage:
    """
    Message of type unknown.
    """


class AbstractTestActor:
    """
    Basic test that an actor should pass

    To use it with an actor that you create you must implement the method actor and actor_start_message
    test function added to this class must take in parameter the two fixtures system and (actor of started_actor)
    """
    @classmethod
    def teardown_class(cls):
        """
        After all test was executed, shutdown the actor system
        """
        while ActorSystem().listen(0.1) is not None:
            continue
        ActorSystem().shutdown()

    @pytest.fixture
    def dummy_pipe(self):
        """
        pipe used between dummy actor and pytest process
        """
        return Pipe()

    @pytest.fixture
    def dummy_pipe_out(self, dummy_pipe):
        """
        pipe used from pytest process to receive dummy actor information
        """
        return dummy_pipe[0]

    @pytest.fixture
    def dummy_pipe_in(self, dummy_pipe):
        """
        pipe used from dummy actor to send information to pytest process
        """
        return dummy_pipe[1]

    @pytest.fixture
    def actor(self):
        """
        This fixture must return the actor class of the tested actor
        """
        raise NotImplementedError()

    @pytest.fixture
    def actor_start_message(self):
        """
        This fixture must return an instance of start message used to start the tested actor
        """
        raise NotImplementedError()

    @pytest.fixture
    def started_actor(self, system, actor, actor_start_message):
        """
        fixture that return and actor that was started with a StartMessage
        """
        system.ask(actor, actor_start_message)
        return actor

    def test_create_an_actor_and_send_it_PingMessage_must_make_it_answer_OKMessage(self, system, actor):
        msg = system.ask(actor, PingMessage('system'), 0.3)
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_create_an_actor_and_send_it_UnknowMessage_must_make_it_answer_ErrorMessage(self, system, actor):
        msg = system.ask(actor, UnknowMessage(), 0.3)
        print(msg)
        assert isinstance(msg, ErrorMessage)

    def test_send_StartMessage_answer_OkMessage(self, system, actor, actor_start_message):
        msg = system.ask(actor, actor_start_message)
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(self, system, started_actor, actor_start_message):
        msg = system.ask(started_actor, actor_start_message)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    def test_send_EndMessage_to_started_actor_make_it_terminate(self, system, started_actor):
        system.tell(started_actor, EndMessage)
        assert not is_actor_alive(system, started_actor)


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


class AbstractTestActorWithDB(AbstractTestActor):
    """
    Base test for actor using a database

    This class add fixtures to communicate with a fake database
    """

    @pytest.fixture
    def pipe(self):
        """
        pipe used to communicate between pytest process and actor
        """
        return Pipe()

    @pytest.fixture
    def pipe_out(self, pipe):
        """
        pipe used from pytest process to receive actor information
        """
        return pipe[0]

    @pytest.fixture
    def pipe_in(self, pipe):
        """
        pipe used from actor process to send information to pytest process
        """
        return pipe[1]

    @pytest.fixture
    def fake_db(self, content, pipe_in):
        """
        Return a FakeDB that will send information through the pipe when using its API
        """
        return FakeDB(content, pipe_in)

    @pytest.fixture
    def crash_db(self):
        """
        Return a FakeDB that will crash when using its connect method
        """
        return CrashDB()

    @pytest.fixture
    def started_actor(self, actor, pipe_out, fake_db, actor_start_message):
        ActorSystem().ask(actor, actor_start_message)
        print(pipe_out.recv())  # remove 'connected' string from Queue
        return actor

    def test_starting_actor_make_it_connect_to_database(self, system, actor, actor_start_message, pipe_out):
        ActorSystem().ask(actor, actor_start_message)
        assert pipe_out.recv() == 'connected'
