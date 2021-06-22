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
import socket
import pickle
import random
from multiprocessing import Pipe

import pytest

from thespian.actors import ActorSystem

from powerapi.message import StartMessage, OKMessage, ErrorMessage
from powerapi.database import BaseDB
from powerapi.report import Report
from .actor.abstract_test_actor import AbstractTestActor
from ..utils import DummyActor


SOCKET_ADDR='/tmp/powerapi_test_socket'

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
    def started_actor(self, actor, pipe_out, fake_db, actor_config):
        ActorSystem().ask(actor, StartMessage(actor_config))
        print(pipe_out.recv())  # remove 'connected' string from Queue
        return actor

    def test_send_StartMessage_answer_OkMessage(self, system, actor, actor_config):
        system.tell(actor, StartMessage(actor_config))
        msg = system.listen()
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(self, system, started_actor, actor_config):
        msg = system.ask(started_actor, StartMessage(actor_config))
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'

    def test_starting_actor_make_it_connect_to_database(self, system, actor, actor_config, pipe_out):
        ActorSystem().ask(actor, StartMessage(actor_config))
        assert pipe_out.recv() == 'connected'


REPORT1 = Report(1, 2, 3)
REPORT2 = Report(3, 4, 5)

class FakeDBError(Exception):
    pass

class FakeDB():

    def __init__(self, content=[], pipe=None, *args, **kwargs):
        BaseDB.__init__(self)
        self._content = content
        self.pipe = pipe
        self.socket_name = SOCKET_ADDR + str(random.randint(1, 10000))
        self.exceptions = [FakeDBError]

    def connect(self):
        self.pipe.send('connected')

    def iter(self, report_model, stream_mode):
        return self._content.__iter__()

    def save(self, report, report_model):
        self.pipe.send(report)

    def save_many(self, reports, report_model):
        self.pipe.send(reports)
