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

from thespian.actors import ActorExitRequest

from powerapi.report import Report
from powerapi.pusher import PusherActor
from powerapi.message import PusherStartMessage, ErrorMessage, EndMessage
from powerapi.test_utils.abstract_test import AbstractTestActorWithDB
from powerapi.test_utils.report.power import POWER_REPORT_1
from powerapi.test_utils.actor import system

###########################################################
#### DU CODE A été enlevié ici, voir le github ############
###########################################################



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
        return PusherStartMessage('system', 'pusher_test', fake_db, None)

    def test_starting_actor_with_db_that_crash_when_connected_must_answer_error_message(self, system, actor, crash_db):
        start_msg = PusherStartMessage('system', 'pusher_test', crash_db, None)
        msg = system.ask(actor, start_msg)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'crash'

    def test_send_one_power_report_to_pusher_make_it_save_to_database(self, system, started_actor, pipe_out):
        system.tell(started_actor, POWER_REPORT_1)
        assert pipe_out.recv() == POWER_REPORT_1

    def test_send_EndMessage_to_started_pusher_make_it_forward_to_supervisor(self, system, started_actor, pipe_out):
        system.tell(started_actor, EndMessage('system'))
        assert isinstance(system.listen(1), EndMessage)



    # @define_buffer_size(0)
    # def test_send_one_report_to_pusher_with_0sized_buffer_make_it_save_the_report(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     assert fake_db.q.get(timeout=1) == [REPORT1]

    # @define_buffer_size(1)
    # def test_send_one_report_to_pusher_with_1sized_buffer_make_it_not_save_the_report(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     with pytest.raises(Empty):
    #         fake_db.q.get(timeout=1)

    # @define_buffer_size(1)
    # def test_send_two_report_to_pusher_with_1sized_buffer_make_it_save_the_reports_in_one_call(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     started_actor.send_data(REPORT2)
    #     assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    # @define_delay(0)
    # def test_send_one_report_to_pusher_with_0delay_make_it_save_the_reports(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     assert fake_db.q.get(timeout=1) == [REPORT1]

    # @define_delay(2000)
    # def test_send_two_report_to_pusher_with_2seconde_delay_make_it_not_save_the_reports(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     started_actor.send_data(REPORT2)
    #     with pytest.raises(Empty):
    #         fake_db.q.get(timeout=1)

    # @define_delay(2000)
    # def test_send_two_report__with_two_second_between_messages_to_pusher_with_2seconde_delay_make_it_save_the_report(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT1)
    #     time.sleep(2)
    #     started_actor.send_data(REPORT2)
    #     assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]

    # @define_buffer_size(1)
    # def test_send_two_report_in_wrong_time_order_to_a_pusher_make_it_save_them_in_good_order(self, started_actor, fake_db):
    #     started_actor.send_data(REPORT2)
    #     started_actor.send_data(REPORT1)
    #     assert fake_db.q.get(timeout=1) == [REPORT1, REPORT2]
