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
import pytest

from multiprocessing import Queue

from powerapi.message import StartMessage
from powerapi.database import BaseDB
from powerapi.report import Report
from .actor.abstract_test_actor import AbstractTestActor

def define_database_content(content):
    def wrap(func):
        setattr(func, '_content', content)
        return func
    return wrap

class AbstractTestActorWithDB(AbstractTestActor):

    @pytest.fixture
    def fake_db(self, content):
        return FakeDB(content)

    @pytest.fixture
    def started_actor(self, init_actor, fake_db):
        init_actor.send_control(StartMessage())
        # remove OkMessage from control socket
        _ = init_actor.receive_control(2000)
        # remove 'connected' string from Queue
        _ = fake_db.q.get(timeout=2)
        return init_actor

    def test_starting_actor_make_it_connect_to_database(self, init_actor, fake_db):
        init_actor.send_control(StartMessage())
        assert fake_db.q.get(timeout=2) == 'connected'


REPORT1 = Report(1, 2, 3)
REPORT2 = Report(3, 4, 5)

class FakeDB(BaseDB):

    def __init__(self, content=[], *args, **kwargs):
        BaseDB.__init__(self)
        self._content = content
        self.q = Queue()

    def connect(self):
        self.q.put('connected', block=False)

    def iter(self, report_model, stream_mode):
        return self._content.__iter__()

    def save(self, report, report_model):
        self.q.put(report, block=False)

    def save_many(self, reports, report_model):
        self.q.put(reports, block=False)
