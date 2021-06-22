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
import time

from multiprocessing import Queue
from mock import Mock

import pytest

from thespian.actors import ActorSystem

from powerapi.message import StartMessage, OKMessage, ErrorMessage, PingMessage
from powerapi.actor import Actor


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
    def system(self):
        syst = ActorSystem(systemBase='multiprocQueueBase')
        yield syst
        syst.shutdown()

    @pytest.fixture
    def actor(self):
        raise NotImplementedError()

    @pytest.fixture
    def actor_config(self):
        raise NotImplementedError()

    @pytest.fixture
    def started_actor(self, system, actor, actor_config):
        system.ask(actor, StartMessage(actor_config))
        return actor

    def test_create_an_actor_and_send_it_PingMessage_must_make_it_answer_OKMessage(self, system, actor):
        msg = system.ask(actor, PingMessage(), 0.3)
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_create_an_actor_and_send_it_UnknowMessage_must_make_it_answer_ErrorMessage(self, system, actor):
        msg = system.ask(actor, UnknowMessage(), 0.3)
        print(msg)
        assert isinstance(msg, ErrorMessage)

