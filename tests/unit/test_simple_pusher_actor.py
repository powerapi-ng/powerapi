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
import pytest

from thespian.actors import ActorExitRequest

from powerapi.report import Report, PowerReport, HWPCReport
from powerapi.pusher import PusherActor
from powerapi.message import PusherStartMessage, ErrorMessage, EndMessage, SimplePusherStartMessage, \
    GetReceivedReportsSimplePusherMessage
from powerapi.simple_pusher import SimplePusherActor
from powerapi.test_utils.abstract_test import AbstractTestActorWithDB, recv_from_pipe, AbstractTestActor
from powerapi.test_utils.report.power import POWER_REPORT_1
from powerapi.test_utils.actor import system

REPORT_TYPE_TO_BE_STORED = HWPCReport
REPORT_TYPE_TO_BE_STORED_2 = PowerReport


class TestSimplePusher(AbstractTestActor):

    @pytest.fixture
    def actor(self, system):
        pusher = system.createActor(SimplePusherActor)
        yield pusher
        system.tell(pusher, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, system, actor):
        return SimplePusherStartMessage('system', 'pusher_test', 2)

    def test_send_one_hwpc_report_to_pusher_make_it_save_it(self, system, started_actor):
        report = HWPCReport.create_empty_report()
        system.tell(started_actor, report)
        reports_message = system.ask(started_actor, GetReceivedReportsSimplePusherMessage('system'))
        system.tell(started_actor, EndMessage('system'))
        assert len(reports_message.reports) == 1
        assert reports_message.reports[0] == report

    def test_send_one_power_report_to_pusher_make_it_save_it(self, system, started_actor):
        report = PowerReport.create_empty_report()
        system.tell(started_actor, report)
        reports_message = system.ask(started_actor, GetReceivedReportsSimplePusherMessage('system'))
        system.tell(started_actor, EndMessage('system'))
        assert len(reports_message.reports) == 1
        assert reports_message.reports[0] == report

    def test_send_EndMessage_to_started_pusher_make_it_forward_to_supervisor(self, system, started_actor):
        system.tell(started_actor, EndMessage('system'))
        assert isinstance(system.listen(1), EndMessage)
