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

from time import sleep
from unittest.mock import patch, Mock

import pytest
from kubernetes import client

from powerapi.processor.pre.k8s.k8s_monitor import MANUAL_CONFIG_MODE, K8sMonitorAgent
from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPodUpdateMetadata, K8sPreProcessorState, ADDED_EVENT, \
    MODIFIED_EVENT
from powerapi.report import HWPCReport
from tests.utils.actor.dummy_actor import DummyActor

LISTENER_AGENT_NAME = 'test_k8s_processor_listener_agent'


def test_override_k8s_api_methods():
    """
    Test the override of k8s client api methods is working. (base of other unit tests)
    """
    v1api_mock = Mock(list_pod_for_all_namespaces=Mock(return_value=Mock()))
    with patch('kubernetes.client.CoreV1Api', return_value=v1api_mock):
        with patch('kubernetes.config.load_kube_config', return_value=Mock()):
            v1_api = client.CoreV1Api()
            ret = v1_api.list_pod_for_all_namespaces()
            assert ret.items != []


class TestK8sMonitor:
    """
    Class for testing a monitor
    """

    @staticmethod
    @pytest.fixture
    def report_to_be_sent():
        """
        This fixture must return the report class for testing
        """
        return K8sPodUpdateMetadata

    @staticmethod
    @pytest.fixture
    def monitor_agent(mocked_watch_initialized, pods_list):
        """
        Return a monitor agent that uses the provided mocked watch
        """
        with patch('kubernetes.client.CoreV1Api', return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch', return_value=mocked_watch_initialized):
                    dummy_actor = DummyActor(name='test_k8s_monitor_actor', pipe=None, message_type=HWPCReport)
                    state = K8sPreProcessorState(dummy_actor, [], [], MANUAL_CONFIG_MODE, 10, 10, '', '')
                    monitor_agent = K8sMonitorAgent(name='test_k8s_monitor', concerned_actor_state=state)
                    yield monitor_agent

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system", "mocked_watch_initialized")
    def test_streaming_query(monitor_agent, expected_events_list_k8s):
        """
        Test that k8s_streaming_query is able to retrieve events related to pods
        """
        result = monitor_agent.k8s_streaming_query()

        assert result == expected_events_list_k8s

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system", "mocked_watch_initialized_unknown_events")
    def test_unknown_events_streaming_query(monitor_agent):
        """
         Test that unknown events are ignored by k8s_streaming_query
         """
        result = monitor_agent.k8s_streaming_query()

        assert result == []

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_monitor_agent_update_metadata_cache_when_events_are_available(monitor_agent, expected_k8s_pod_update_metadata):
        """
        Test that the monitor updates metadata cache when events are available
        """
        expected_pods_labels_size = 0
        expected_containers_ids_size = 0
        for current_metadata in expected_k8s_pod_update_metadata:
            if current_metadata.event in [ADDED_EVENT, MODIFIED_EVENT]:
                expected_pods_labels_size += 1
                expected_containers_ids_size += len(current_metadata.containers_id)

        monitor_agent.start()

        sleep(1)

        monitor_agent.stop_monitoring.set()

        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_labels) == \
               expected_pods_labels_size  # There is a event if each type ADDED, DELETED and MODIFIED

        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_containers) == \
               expected_pods_labels_size

        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.containers_pod) == \
               expected_containers_ids_size

        assert monitor_agent.stop_monitoring.is_set()

    @staticmethod
    def test_stop_monitor_agent_works(monitor_agent):
        """
        Test that monitor agent is correctly stopped when the flag related to the monitoring is changed
        """

        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_labels) == 0
        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_containers) == 0
        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.containers_pod) == 0
        assert not monitor_agent.stop_monitoring.is_set()

        monitor_agent.start()

        sleep(1)

        monitor_agent.stop_monitoring.set()

        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_labels) > 0
        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.pod_containers) > 0
        assert len(monitor_agent.concerned_actor_state.metadata_cache_manager.containers_pod) > 0
        assert monitor_agent.stop_monitoring.is_set()
