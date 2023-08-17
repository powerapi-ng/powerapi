# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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

# pylint: disable=R6301,W0613,W0221

from unittest.mock import patch, Mock

import pytest

from kubernetes import client

from powerapi.message import K8sPodUpdateMessage
from powerapi.processor.k8s.k8s_monitor_actor import local_config, MANUAL_CONFIG_MODE, \
    K8sMonitorAgentActor
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe

LISTENER_AGENT_NAME = 'test_k8s_processor_listener_agent'


def test_load_local_config():
    """
    Test that load_config works correctly
    """
    with patch('kubernetes.client.CoreV1Api',
               return_value=Mock(list_pod_for_all_namespaces=Mock(
                   return_value={'pod': 'some infos about the pod...'}))):
        with patch('kubernetes.config.load_kube_config', return_value=Mock()):
            local_config()

            # Just check we are able to make a request and get a non-empty response
            v1_api = client.CoreV1Api()
            ret = v1_api.list_pod_for_all_namespaces()
            assert ret.items != []


class TestK8sMonitor(AbstractTestActor):
    """
    Class for testing a monitor actor
    """

    @pytest.fixture
    def report_to_be_sent(self):
        """
        This fixture must return the report class for testing
        """
        return K8sPodUpdateMessage

    @pytest.fixture
    def actor(self, started_fake_target_actor, mocked_watch_initialized, pods_list):
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch', return_value=mocked_watch_initialized):
                    yield K8sMonitorAgentActor(name='test_k8s_monitor_actor',
                                               listener_agent=started_fake_target_actor,
                                               k8s_api_mode=MANUAL_CONFIG_MODE)

    def test_streaming_query(self, started_actor, pods_list, expected_events_list_k8s, mocked_watch_initialized,
                             shutdown_system):
        """
        Test that k8s_streaming_query is able to retrieve events related to pods
        """
        result = started_actor.k8s_streaming_query(timeout_seconds=5, k8sapi_mode=MANUAL_CONFIG_MODE)

        assert result == expected_events_list_k8s

    def test_unknown_events_streaming_query(self, pods_list, mocked_watch_initialized_unknown_events,
                                            started_actor, shutdown_system):
        """
         Test that unknown events are ignored by k8s_streaming_query
         """
        result = started_actor.k8s_streaming_query(timeout_seconds=5, k8sapi_mode=MANUAL_CONFIG_MODE)

        assert result == []

    def test_monitor_send_message_k8s_pod_update_message_when_events_are_available(self, started_actor,
                                                                                   expected_k8s_pod_update_messages,
                                                                                   dummy_pipe_out, shutdown_system):
        """
        Test that the monitor sends to the target an update message when events are available
        """
        messages_found = 0

        for _ in range(len(expected_k8s_pod_update_messages)):
            result = recv_from_pipe(dummy_pipe_out, 2)
            got_message = result[1]
            assert isinstance(got_message, K8sPodUpdateMessage)

            for expected_message in expected_k8s_pod_update_messages:

                if got_message == expected_message:
                    messages_found += 1
                    break

        assert messages_found == len(expected_k8s_pod_update_messages)
