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
import pytest

from thespian.actors import ActorExitRequest

from powerapi.report import Report
from powerapi.pusher import PusherActor
from powerapi.message import PusherStartMessage, ErrorMessage, EndMessage
from powerapi.test_utils.abstract_test import AbstractTestActorWithDB, recv_from_pipe
from powerapi.test_utils.report.power import POWER_REPORT_1
from powerapi.test_utils.actor import system

class TestPuller(AbstractTestActorWithDB):

    @pytest.fixture
    def actor(self, system):
        pusher = system.createActor(PusherActor)
        yield pusher
        system.tell(pusher, ActorExitRequest())

    @pytest.fixture
    def content(self):
        """
        set an empty content for database
        """
        return []

    @pytest.fixture
    def actor_start_message(self, system, actor, fake_db):
        return PusherStartMessage('system', 'pusher_test', fake_db)

    def test_starting_actor_with_db_that_crash_when_connected_must_answer_error_message(self, system, actor, crash_db):
        start_msg = PusherStartMessage('system', 'pusher_test', crash_db)
        msg = system.ask(actor, start_msg)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'crash'

    def test_send_one_power_report_to_pusher_make_it_save_to_database(self, system, started_actor, pipe_out):
        system.tell(started_actor, POWER_REPORT_1)
        assert recv_from_pipe(pipe_out, 0.5) == POWER_REPORT_1

    def test_send_EndMessage_to_started_pusher_make_it_forward_to_supervisor(self, system, started_actor, pipe_out):
        system.tell(started_actor, EndMessage('system'))
        assert isinstance(system.listen(1), EndMessage)
