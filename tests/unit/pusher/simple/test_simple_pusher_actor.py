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
from time import sleep

import pytest

from powerapi.message import PoisonPillMessage, GetReceivedReportsSimplePusherMessage
from powerapi.pusher.simple.simple_pusher_actor import SimplePusherActor
from powerapi.report import PowerReport, HWPCReport
from tests.unit.actor.abstract_test_actor import is_actor_alive, AbstractTestActor

REPORT_TYPE_TO_BE_STORED = HWPCReport
REPORT_TYPE_TO_BE_STORED_2 = PowerReport
NUMBER_OF_REPORTS_TO_STORE = 100


class TestSimplePusher(AbstractTestActor):

    @pytest.fixture
    def actor(self):
        return SimplePusherActor('pusher_test', NUMBER_OF_REPORTS_TO_STORE)

    def test_send_one_hwpc_report_to_pusher_make_it_save_it(self, started_actor):
        report = HWPCReport.create_empty_report()
        started_actor.send_data(report)
        started_actor.send_control(GetReceivedReportsSimplePusherMessage('system'))
        message_reports = started_actor.receive_control(2000)
        assert len(message_reports.reports) == 1
        assert message_reports.reports[0] == report

    def test_send_one_power_report_to_pusher_make_it_save_it(self, started_actor):
        report = PowerReport.create_empty_report()
        started_actor.send_data(report)
        sleep(2)
        started_actor.send_control(GetReceivedReportsSimplePusherMessage('system'))
        message_reports = started_actor.receive_control(2000)
        assert len(message_reports.reports) == 1
        assert message_reports.reports[0] == report

    def test_starting_actor_terminate_itself_after_poison_message_reception(self, started_actor):
        started_actor.send_control(PoisonPillMessage())
        assert not is_actor_alive(started_actor)

    def test_check_actor_still_alive_if_x_messages_are_no_still_received(self, started_actor):
        sent = 0

        while sent < NUMBER_OF_REPORTS_TO_STORE - 1:
            report = PowerReport.create_empty_report()
            sent += 1
            started_actor.send_data(report)

        assert is_actor_alive(started_actor)
