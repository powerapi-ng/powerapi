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
import time
from multiprocessing import Pipe

import pytest

from powerapi.message import OKMessage, ErrorMessage, PingMessage, EndMessage, PoisonPillMessage, StartMessage
from tests.unit.actor.abstract_test_actor import CrashMessage

from .db import FakeDB, CrashDB
from .dummy_actor import DummyActor
from ..actor import NotConnectedException

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


# TODO HAS TO DISSAPEAR
class AbstractTestActor:
    """
    Basic test that an actor should pass

    To use it with an actor that you create you must implement the method actor and actor_start_message
    test function added to this class must take in parameter the two fixtures system and (actor of started_actor)
    """

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
        # ActorSystem().ask(actor, actor_start_message)
        print(pipe_out.recv())  # remove 'connected' string from Queue
        return actor

    def test_starting_actor_make_it_connect_to_database(self, system, actor, actor_start_message, pipe_out):
        # ActorSystem().ask(actor, actor_start_message)
        assert pipe_out.recv() == 'connected'
