# Copyright (c) 2023, Inria
# Copyright (c) 2023, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

import logging
from datetime import datetime
from unittest.mock import Mock

import pytest

from powerapi.processor.pre.k8s import K8sPreProcessorActor
from powerapi.report import HWPCReport
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe


class TestK8sProcessor(AbstractTestActor):
    """
    Class for testing a K8s Processor Actor
    """

    @pytest.fixture
    def report_to_be_sent(self):
        """
        This fixture must return the report class for testing
        """
        return HWPCReport

    @pytest.fixture
    def actor(self, request):
        fx_started_fake_target_actor = request.getfixturevalue('started_fake_target_actor')
        fx_initialized_metadata_cache_manager = request.getfixturevalue('initialized_metadata_cache_manager')
        actor_name = 'test_k8s_processor_actor'
        target_actors = [fx_started_fake_target_actor]
        api_mode = 'manual'
        actor = K8sPreProcessorActor(actor_name, target_actors, [], api_mode, level_logger=logging.DEBUG)

        actor.state.initialize_metadata_cache_manager = lambda: True
        actor.state.metadata_cache_manager = fx_initialized_metadata_cache_manager
        actor.state.manager = Mock()
        actor.state.monitor_agent = Mock()
        yield actor

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_send_hwpc_report_with_non_k8s_target(started_actor, dummy_pipe_out):
        """
        Test sending a HWPCReport with non-k8s target name.
        """
        report = HWPCReport(datetime.now(), 'pytest', 'non-k8s-container', {}, {})
        started_actor.send_data(report)

        _, result = recv_from_pipe(dummy_pipe_out, 5)
        assert result == report
