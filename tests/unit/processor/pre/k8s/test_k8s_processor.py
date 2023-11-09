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

# pylint: disable=R6301,W0221,W0613

import logging
from copy import deepcopy
from time import sleep
from unittest.mock import patch, Mock

import pytest

from powerapi.processor.pre.k8s.k8s_monitor import MANUAL_CONFIG_MODE, ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT, \
    K8sMonitorAgent
from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorActor, K8sPodUpdateMetadata
from powerapi.processor.pre.k8s.k8s_pre_processor_handlers import clean_up_container_id, POD_NAMESPACE_METADATA_KEY, \
    POD_NAME_METADATA_KEY
from powerapi.report import HWPCReport
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe
from tests.unit.processor.conftest import MockedWatch, FakePod, FakeMetadata, FakeStatus, FakeContainerStatus
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets

DISPATCHER_NAME = 'test_k8s_processor_dispatcher'


def get_metadata_from_event(basic_event: dict):
    """
    Create a K8sPodUpdateMetadata from a dict containing the event info
    :param dict basic_event : The event information
    """
    containers_id = []

    for current_fake_container_status in basic_event['object'].status.container_statuses:
        index_id = current_fake_container_status.container_id.index('://')
        current_container_id = current_fake_container_status.container_id[index_id +
                                                                          len('://'):
                                                                          len(current_fake_container_status.container_id
                                                                              )]
        containers_id.append(current_container_id)

    return K8sPodUpdateMetadata(event=basic_event['type'],
                                namespace=basic_event['object'].metadata.namespace,
                                pod=basic_event['object'].metadata.name,
                                containers_id=containers_id,
                                labels=basic_event['object'].metadata.labels)


def test_clean_up_id_docker():
    """
    Test that the cleanup of the docker id works correctly
    """
    r = clean_up_container_id(
        "/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod435532e3_546d_45e2_8862_d3c7b320d2d9.slice/"
        "docker-68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a.scope")

    assert r == "68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a"


def test_clean_up_id_othercri():
    """
    Test that the cleanup of the docker id works correctly
    """
    r = clean_up_container_id(
        "/kubepods/besteffort/pod42006d2c-cad7-4575-bfa3-91848a558743/ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5")

    assert r == "ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5"


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
    def basic_added_event_k8s(self):
        """
        Return a basic ADDED event and its related information
        """
        return {
            'type': ADDED_EVENT,
            'object': FakePod(
                metadata=FakeMetadata(name='test_k8s_processor_pod', namespace='test_k8s_processor_namespace',
                                      labels={'l1': 'v1', 'l2': 'v2', 'l3': 'v3', 'l4': 'v4', 'l5': 'v5'}),
                status=FakeStatus(container_statuses=[FakeContainerStatus(
                    container_id='/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_1_added'),
                    FakeContainerStatus(
                        container_id='/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_2_added'),
                    FakeContainerStatus(
                        container_id='/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_3_added'),
                    FakeContainerStatus(
                        container_id='/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_4_added')])
            )
        }

    @pytest.fixture
    def basic_modified_event_k8s(self):
        """
        Return a basic MODIFIED event and its related information
        """
        return {
            'type': MODIFIED_EVENT,
            'object': FakePod(
                metadata=FakeMetadata(name='test_k8s_processor_pod', namespace='test_k8s_processor_namespace',
                                      labels={'l1_m': 'v1', 'l2_m': 'v2', 'l3_m': 'v3', 'l4_m': 'v4', 'l5_m': 'v5'}),
                status=FakeStatus(container_statuses=[FakeContainerStatus(
                    container_id='/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_1_modified'),
                    FakeContainerStatus(
                        container_id='/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_2_modified'),
                    FakeContainerStatus(
                        container_id='/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_3_modified'),
                    FakeContainerStatus(
                        container_id='/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_4_modified')])
            )
        }

    @pytest.fixture
    def basic_deleted_event_k8s(self):
        """
        Return a basic DELETED event and its related information
        """
        return {
            'type': DELETED_EVENT,
            'object': FakePod(
                metadata=FakeMetadata(name='test_k8s_processor_pod', namespace='test_k8s_processor_namespace',
                                      labels=[]),
                status=None
            )
        }

    @pytest.fixture
    def basic_unknown_event_k8s(self):
        """
        Return a basic DELETED event and its related information
        """
        return {
            'type': 'Unknown Event',
            'object': FakePod(
                metadata=FakeMetadata(name='test_k8s_processor_pod', namespace='test_k8s_processor_namespace',
                                      labels=[]),
                status=None
            )
        }

    @pytest.fixture()
    def hwpc_report(self, basic_added_event_k8s):
        """
        Return a HWPC Report
        """
        json_input = extract_rapl_reports_with_2_sockets(1)[0]
        report = HWPCReport.from_json(json_input)
        report.target = basic_added_event_k8s['object'].status.container_statuses[0].container_id

        return report

    @pytest.fixture()
    def hwpc_report_with_metadata(self, hwpc_report, basic_added_event_k8s):
        """
        Return a HWPC report with metadata
        """
        update_metadata_cache_added_event = get_metadata_from_event(basic_event=basic_added_event_k8s)
        hwpc_report_with_metadata = deepcopy(hwpc_report)

        hwpc_report_with_metadata.metadata[POD_NAMESPACE_METADATA_KEY] = \
            update_metadata_cache_added_event.namespace
        hwpc_report_with_metadata.metadata[POD_NAME_METADATA_KEY] = update_metadata_cache_added_event.pod

        for label_name, label_value in update_metadata_cache_added_event.labels.items():
            hwpc_report_with_metadata.metadata[f"label_{label_name}"] = label_value

        return hwpc_report_with_metadata

    @pytest.fixture
    def actor(self, started_fake_target_actor, pods_list, mocked_watch_initialized):
        return K8sPreProcessorActor(name='test_k8s_processor_actor', ks8_api_mode=MANUAL_CONFIG_MODE,
                                    target_actors=[started_fake_target_actor],
                                    level_logger=logging.DEBUG)

    @pytest.fixture
    def mocked_monitor_added_event(self, actor, basic_added_event_k8s, pods_list):
        """
        Return a mocked monitor that produces an added event
        """
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch',
                           return_value=MockedWatch(events=[basic_added_event_k8s])):
                    yield K8sMonitorAgent(name='test_update_metadata_cache_with_added_event_monitor_agent',
                                          concerned_actor_state=actor.state)

    @pytest.fixture
    def mocked_monitor_modified_event(self, actor, basic_modified_event_k8s, pods_list):
        """
        Return a mocked monitor that produces a modified event
        """
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch',
                           return_value=MockedWatch(events=[basic_modified_event_k8s])):
                    yield K8sMonitorAgent(name='test_update_metadata_cache_with_added_event_monitor_agent',
                                          concerned_actor_state=actor.state)

    @pytest.fixture
    def mocked_monitor_deleted_event(self, actor, basic_deleted_event_k8s, pods_list):
        """
        Return a mocked monitor that produces a deleted event
        """
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch',
                           return_value=MockedWatch(events=[basic_deleted_event_k8s])):
                    yield K8sMonitorAgent(name='test_update_metadata_cache_with_added_event_monitor_agent',
                                          concerned_actor_state=actor.state)

    @pytest.fixture
    def mocked_monitor_unknown_event(self, actor, basic_added_event_k8s, basic_unknown_event_k8s, pods_list):
        """
        Return a mocked monitor that produces an unknown event
        """
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch',
                           return_value=MockedWatch(events=[basic_unknown_event_k8s, basic_added_event_k8s])):
                    yield K8sMonitorAgent(name='test_update_metadata_cache_with_added_event_monitor_agent',
                                          concerned_actor_state=actor.state)

    def test_update_metadata_cache_with_added_event(self, mocked_monitor_added_event, started_actor,
                                                    basic_added_event_k8s, shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of an added event
        """
        metadata_for_update = get_metadata_from_event(basic_event=basic_added_event_k8s)
        mocked_monitor_added_event.start()
        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_added_event.stop_monitoring.set()

    def test_update_metadata_cache_with_modified_event(self, mocked_monitor_modified_event, started_actor,
                                                       basic_modified_event_k8s, shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of a modified event
        """

        metadata_for_update = get_metadata_from_event(basic_event=basic_modified_event_k8s)
        mocked_monitor_modified_event.start()
        sleep(10)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_modified_event.stop_monitoring.set()

    def test_update_metadata_cache_with_deleted_event(self, mocked_monitor_deleted_event, started_actor,
                                                      basic_deleted_event_k8s, shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of a deleted event
        """
        mocked_monitor_deleted_event.start()
        sleep(0.5)

        result = started_actor.state.metadata_cache_manager

        assert len(result.pod_labels) == 0
        assert len(result.pod_containers) == 0
        assert len(result.containers_pod) == 0

        mocked_monitor_deleted_event.stop_monitoring.set()

    def test_update_metadata_cache_with_unknown_event_does_not_modify_it(self, mocked_monitor_unknown_event,
                                                                         started_actor,
                                                                         basic_added_event_k8s,
                                                                         shutdown_system):
        """
        Test that metadata_cache is not updated when a reception of an unknown event
        """
        metadata_for_update = get_metadata_from_event(basic_event=basic_added_event_k8s)
        mocked_monitor_unknown_event.start()

        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_unknown_event.stop_monitoring.set()

    def test_add_metadata_to_hwpc_report(self, mocked_monitor_added_event,
                                         started_actor,
                                         hwpc_report, hwpc_report_with_metadata,
                                         dummy_pipe_out,
                                         shutdown_system):
        """
          Test that a HWPC report is modified with the correct metadata
          """
        mocked_monitor_added_event.start()

        sleep(1)

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result[1] == hwpc_report_with_metadata

        mocked_monitor_added_event.stop_monitoring.set()

    def test_add_metadata_to_hwpc_report_does_not_modify_report_with_unknown_container_id(self,
                                                                                          mocked_monitor_added_event,
                                                                                          started_actor,
                                                                                          hwpc_report,
                                                                                          dummy_pipe_out,
                                                                                          shutdown_system):
        """
         Test that a HWPC report is not modified with an unknown container id
         """

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 4)

        assert result[1] == hwpc_report
