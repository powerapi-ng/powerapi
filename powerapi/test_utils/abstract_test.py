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
from multiprocessing import Pipe

import pytest

from thespian.actors import ActorSystem, ActorExitRequest

from powerapi.message import OKMessage, ErrorMessage, PingMessage
from powerapi.actor import Actor

from .db import FakeDB
from .dummy_actor import DummyActor

LOGGER_NAME='thespian_test_logger'

class UnknowMessage:
    pass

class AbstractTestActor:
    """
    test basic actor behaviour
    """
    @classmethod 
    def teardown_class(cls):
        while ActorSystem().listen(0.1) != None:
            continue
        ActorSystem().shutdown()

    @pytest.fixture
    def logger(self, system):
        logger_actor = system.createActor(DummyActor, globalName=LOGGER_NAME)
        system.tell(logger_actor, 'logger')
        yield logger_actor
        system.tell(logger_actor, ActorExitRequest())

    @pytest.fixture
    def system(self):
        syst = ActorSystem(systemBase='multiprocQueueBase')
        yield syst
        syst.shutdown()

    @pytest.fixture
    def actor(self):
        raise NotImplementedError()

    @pytest.fixture
    def actor_start_message(self):
        raise NotImplementedError()

    @pytest.fixture
    def started_actor(self, system, actor, actor_start_message):
        system.ask(actor, actor_start_message)
        return actor

    def test_create_an_actor_and_send_it_PingMessage_must_make_it_answer_OKMessage(self, system, actor):
        msg = system.ask(actor, PingMessage(), 0.3)
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_create_an_actor_and_send_it_UnknowMessage_must_make_it_answer_ErrorMessage(self, system, actor):
        msg = system.ask(actor, UnknowMessage(), 0.3)
        print(msg)
        assert isinstance(msg, ErrorMessage)

def define_database_content(content):
    def wrap(func):
        setattr(func, '_content', content)
        return func
    return wrap

class AbstractTestActorWithDB(AbstractTestActor):

    @pytest.fixture
    def pipe(self):
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
        return FakeDB(content, pipe_in)

    @pytest.fixture
    def started_actor(self, actor, pipe_out, fake_db, actor_start_message):
        ActorSystem().ask(actor, actor_start_message)
        print(pipe_out.recv())  # remove 'connected' string from Queue
        return actor

    def test_send_StartMessage_answer_OkMessage(self, system, actor, actor_start_message):
        system.tell(actor, actor_start_message)
        msg = system.listen()
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(self, system, started_actor, actor_start_message):
        msg = system.ask(started_actor, actor_start_message)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    def test_starting_actor_make_it_connect_to_database(self, system, actor, actor_start_message, pipe_out):
        ActorSystem().ask(actor, actor_start_message)
        assert pipe_out.recv() == 'connected'
