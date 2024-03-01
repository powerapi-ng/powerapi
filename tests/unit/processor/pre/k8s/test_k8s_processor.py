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
import os
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
KUBERNETES_CLIENT_API_REFERENCE = 'kubernetes.client.CoreV1Api'
KUBERNETES_LOAD_CONFIG_REFERENCE = 'kubernetes.config.load_kube_config'
KUBERNETES_WATCH_REFERENCE = 'kubernetes.watch.Watch'


def get_metadata_from_event(basic_event: dict) -> K8sPodUpdateMetadata:
    """
    Create a K8sPodUpdateMetadata from a dict containing the event info
    :param dict basic_event : The event information
    """
    containers_id = []

    for current_fake_container_status in basic_event['object'].status.container_statuses:
        _, _, container_id = current_fake_container_status.container_id.partition('://')  # CRI, ://, container_id
        containers_id.append(container_id)

    return K8sPodUpdateMetadata(basic_event['type'], basic_event['object'].metadata.namespace,
                                basic_event['object'].metadata.name, containers_id, basic_event['object'].metadata.labels)


def test_extract_docker_container_id_from_cgroups_v2_path():
    """
    Test the container id extraction from a Kubernetes cgroups v2 path.
    """
    path = os.path.join(
        "/kubepods.slice",
        "kubepods-burstable.slice",  # QoS
        "kubepods-burstable-pod435532e3_546d_45e2_8862_d3c7b320d2d9.slice",  # POD
        "docker-68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a.scope"  # Container
    )

    assert clean_up_container_id(path) == "68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a"


def test_extract_docker_container_id_from_cgroups_v1_path():
    """
    Test the container id extraction from a Kubernetes cgroups v1 path.
    """
    path = os.path.join(
        '/kubepods',
        'besteffort',  # QoS
        'pod42006d2c-cad7-4575-bfa3-91848a558743',  # POD
        'ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5'  # Container
    )

    assert clean_up_container_id(path) == "ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5"


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

    @staticmethod
    @pytest.fixture
    def basic_added_event_k8s():
        """
        Return a basic ADDED event and its related information
        """
        labels = {'l1': 'v1', 'l2': 'v2', 'l3': 'v3', 'l4': 'v4', 'l5': 'v5'}
        fake_metadata = FakeMetadata('test_k8s_processor_pod', 'test_k8s_processor_namespace', labels)
        return {
            'type': ADDED_EVENT,
            'object': FakePod(fake_metadata, FakeStatus([
                FakeContainerStatus('/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_1_added'),
                FakeContainerStatus('/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_2_added'),
                FakeContainerStatus('/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_3_added'),
                FakeContainerStatus('/kpods/t_q/pod_test_k8s_processor_pod_added://test_cid_4_added')])
            )
        }

    @staticmethod
    @pytest.fixture
    def basic_modified_event_k8s():
        """
        Return a basic MODIFIED event and its related information
        """
        labels = {'l1_m': 'v1', 'l2_m': 'v2', 'l3_m': 'v3', 'l4_m': 'v4', 'l5_m': 'v5'}
        fake_metadata = FakeMetadata('test_k8s_processor_pod', 'test_k8s_processor_namespace', labels)
        return {
            'type': MODIFIED_EVENT,
            'object': FakePod(fake_metadata, FakeStatus([
                FakeContainerStatus('/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_1_modified'),
                FakeContainerStatus('/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_2_modified'),
                FakeContainerStatus('/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_3_modified'),
                FakeContainerStatus('/kp/t_q/pod_test_k8s_processor_pod_added://test_cid_4_modified')])
            )
        }

    @staticmethod
    @pytest.fixture
    def basic_deleted_event_k8s():
        """
        Return a basic DELETED event and its related information
        """
        return {
            'type': DELETED_EVENT,
            'object': FakePod(
                FakeMetadata('test_k8s_processor_pod', 'test_k8s_processor_namespace', {}),
                FakeStatus([])
            )
        }

    @staticmethod
    @pytest.fixture
    def basic_unknown_event_k8s():
        """
        Return a basic DELETED event and its related information
        """
        return {
            'type': 'Unknown Event',
            'object': FakePod(
                FakeMetadata('test_k8s_processor_pod', 'test_k8s_processor_namespace', {}),
                FakeStatus([])
            )
        }

    @staticmethod
    @pytest.fixture()
    def hwpc_report(basic_added_event_k8s):
        """
        Return a HWPC Report
        """
        json_input = extract_rapl_reports_with_2_sockets(1)[0]
        report = HWPCReport.from_json(json_input)
        report.target = basic_added_event_k8s['object'].status.container_statuses[0].container_id

        return report

    @staticmethod
    @pytest.fixture()
    def hwpc_report_with_metadata(hwpc_report, basic_added_event_k8s):
        """
        Return a HWPC report with metadata
        """
        update_metadata_cache_added_event = get_metadata_from_event(basic_event=basic_added_event_k8s)
        hwpc_report_with_metadata = deepcopy(hwpc_report)

        hwpc_report_with_metadata.metadata[POD_NAMESPACE_METADATA_KEY] = update_metadata_cache_added_event.namespace
        hwpc_report_with_metadata.metadata[POD_NAME_METADATA_KEY] = update_metadata_cache_added_event.pod

        for label_name, label_value in update_metadata_cache_added_event.labels.items():
            hwpc_report_with_metadata.metadata[f"label_{label_name}"] = label_value

        return hwpc_report_with_metadata

    @staticmethod
    @pytest.fixture()
    def hwpc_report_empty_metadata_values(hwpc_report):
        """
        Return a HWPC report with metadata values (pod namespace and pod name)
        """
        hwpc_report_with_empty_metadata_values = deepcopy(hwpc_report)

        hwpc_report_with_empty_metadata_values.metadata[POD_NAMESPACE_METADATA_KEY] = ""
        hwpc_report_with_empty_metadata_values.metadata[POD_NAME_METADATA_KEY] = ""

        return hwpc_report_with_empty_metadata_values

    @pytest.fixture
    def actor(self, request):
        fx_started_fake_target_actor = request.getfixturevalue('started_fake_target_actor')
        return K8sPreProcessorActor('test_k8s_processor_actor', MANUAL_CONFIG_MODE,
                                    [fx_started_fake_target_actor], level_logger=logging.DEBUG)

    @staticmethod
    @pytest.fixture
    def mocked_monitor_added_event(actor, basic_added_event_k8s, pods_list):
        """
        Return a mocked monitor that produces an added event
        """
        with patch(KUBERNETES_CLIENT_API_REFERENCE, return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch(KUBERNETES_LOAD_CONFIG_REFERENCE, return_value=Mock()):
                with patch(KUBERNETES_WATCH_REFERENCE, return_value=MockedWatch(events=[basic_added_event_k8s])):
                    yield K8sMonitorAgent('test_update_metadata_cache_with_added_event_monitor_agent', actor.state)

    @staticmethod
    @pytest.fixture
    def mocked_monitor_modified_event(actor, basic_modified_event_k8s, pods_list):
        """
        Return a mocked monitor that produces a modified event
        """
        with patch(KUBERNETES_CLIENT_API_REFERENCE, return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch(KUBERNETES_LOAD_CONFIG_REFERENCE, return_value=Mock()):
                with patch(KUBERNETES_WATCH_REFERENCE, return_value=MockedWatch(events=[basic_modified_event_k8s])):
                    yield K8sMonitorAgent('test_update_metadata_cache_with_added_event_monitor_agent', actor.state)

    @staticmethod
    @pytest.fixture
    def mocked_monitor_deleted_event(actor, basic_deleted_event_k8s, pods_list):
        """
        Return a mocked monitor that produces a deleted event
        """
        with patch(KUBERNETES_CLIENT_API_REFERENCE, return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch(KUBERNETES_LOAD_CONFIG_REFERENCE, return_value=Mock()):
                with patch(KUBERNETES_WATCH_REFERENCE, return_value=MockedWatch(events=[basic_deleted_event_k8s])):
                    yield K8sMonitorAgent('test_update_metadata_cache_with_added_event_monitor_agent', actor.state)

    @staticmethod
    @pytest.fixture
    def mocked_monitor_unknown_event(actor, basic_added_event_k8s, basic_unknown_event_k8s, pods_list):
        """
        Return a mocked monitor that produces an unknown event
        """
        with patch(KUBERNETES_CLIENT_API_REFERENCE, return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch(KUBERNETES_LOAD_CONFIG_REFERENCE, return_value=Mock()):
                with patch(KUBERNETES_WATCH_REFERENCE, return_value=MockedWatch(events=[basic_unknown_event_k8s, basic_added_event_k8s])):
                    yield K8sMonitorAgent('test_update_metadata_cache_with_added_event_monitor_agent', actor.state)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_update_metadata_cache_with_added_event(mocked_monitor_added_event, started_actor, basic_added_event_k8s):
        """
        Test that metadata_cache is correctly updated when a reception of an added event
        """
        metadata_for_update = get_metadata_from_event(basic_added_event_k8s)
        mocked_monitor_added_event.start()
        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_added_event.stop_monitoring.set()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    @pytest.mark.skip(reason='Flaky test that fails sometimes because of multiprocessing')
    def test_update_metadata_cache_with_modified_event(mocked_monitor_modified_event, started_actor, basic_modified_event_k8s):
        """
        Test that metadata_cache is correctly updated when a reception of a modified event
        """
        metadata_for_update = get_metadata_from_event(basic_modified_event_k8s)
        mocked_monitor_modified_event.start()
        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == \
               metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_modified_event.stop_monitoring.set()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_update_metadata_cache_with_deleted_event(mocked_monitor_deleted_event, started_actor):
        """
        Test that metadata_cache is correctly updated when a reception of a deleted event
        """
        mocked_monitor_deleted_event.start()
        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert len(result.pod_labels) == 0
        assert len(result.pod_containers) == 0
        assert len(result.containers_pod) == 0

        mocked_monitor_deleted_event.stop_monitoring.set()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_update_metadata_cache_with_unknown_event_does_not_modify_it(mocked_monitor_unknown_event, started_actor, basic_added_event_k8s):
        """
        Test that metadata_cache is not updated when a reception of an unknown event
        """
        metadata_for_update = get_metadata_from_event(basic_added_event_k8s)
        mocked_monitor_unknown_event.start()
        sleep(1)

        result = started_actor.state.metadata_cache_manager

        assert result.pod_labels[(metadata_for_update.namespace, metadata_for_update.pod)] == metadata_for_update.labels
        assert result.pod_containers[(metadata_for_update.namespace, metadata_for_update.pod)] == metadata_for_update.containers_id

        for container_id in metadata_for_update.containers_id:
            assert result.containers_pod[container_id] == (metadata_for_update.namespace, metadata_for_update.pod)

        mocked_monitor_unknown_event.stop_monitoring.set()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    def test_add_metadata_to_hwpc_report(mocked_monitor_added_event, started_actor, hwpc_report, hwpc_report_with_metadata, dummy_pipe_out):
        """
        Test that a HWPC report is modified with the correct metadata
        """
        mocked_monitor_added_event.start()
        sleep(1)

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 5)

        assert result[1] == hwpc_report_with_metadata

        mocked_monitor_added_event.stop_monitoring.set()

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system", "mocked_monitor_added_event")
    def test_add_metadata_to_hwpc_report_not_modified_with_unknown_container_id(started_actor, hwpc_report, dummy_pipe_out, hwpc_report_empty_metadata_values):
        """
        Test that a HWPC report is not modified with an unknown container id
        """

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 5)

        assert result[1] == hwpc_report_empty_metadata_values
