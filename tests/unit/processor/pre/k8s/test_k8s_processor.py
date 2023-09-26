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
from unittest.mock import patch, Mock

import pytest

from powerapi.message import K8sPodUpdateMessage
from powerapi.processor.pre.k8s.k8s_monitor_actor import MANUAL_CONFIG_MODE, ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT
from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorActor
from powerapi.processor.pre.k8s.k8s_pre_processor_handlers import clean_up_container_id, POD_NAMESPACE_METADATA_KEY, \
    POD_NAME_METADATA_KEY
from powerapi.report import HWPCReport
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe
from tests.unit.processor.conftest import PipeMetadataCache
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets

DISPATCHER_NAME = 'test_k8s_processor_dispatcher'


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
    def multiprocess_metadata_cache_empty(self, dummy_pipe_in):
        """
        Create a metadata cache that send the object once it is modified via a pipe
        """
        return PipeMetadataCache(name='test_k8s_process', level_logger=logging.DEBUG, pipe=dummy_pipe_in)

    @pytest.fixture
    def update_metadata_cache_message_added_event(self):
        """
        Create a update message
        """
        return K8sPodUpdateMessage(sender_name='test_k8s_processor_added',
                                   event=ADDED_EVENT,
                                   namespace='test_k8s_processor_namespace',
                                   pod='test_k8s_processor_pod',
                                   containers_id=[
                                       'test_cid_1_added',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_2_added',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_3_added',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_4_added'],
                                   labels={'l1': 'v1', 'l2': 'v2', 'l3': 'v3'})

    @pytest.fixture
    def update_metadata_cache_message_modified_event(self):
        """
        Create a update message
        """
        return K8sPodUpdateMessage(sender_name='test_k8s_processor_modified',
                                   event=MODIFIED_EVENT,
                                   namespace='test_k8s_processor_namespace',
                                   pod='test_k8s_processor_pod',
                                   containers_id=[
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_1_modified',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_2_modified',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_3_modified',
                                       '/kubepods/test_qos/pod_test_k8s_processor_pod_added/test_cid_4_modified'],
                                   labels={'l1': 'v1_modified', 'l2_modified': 'v2_modified',
                                           'l3_modified': 'v3_modified'})

    @pytest.fixture
    def update_metadata_cache_message_deleted_event(self):
        """
        Create a update message with DELETED as event
        """
        return K8sPodUpdateMessage(sender_name='test_k8s_processor_deleted',
                                   event=DELETED_EVENT,
                                   namespace='test_k8s_processor_namespace',
                                   pod='test_k8s_processor_pod')

    @pytest.fixture
    def update_metadata_cache_message_unknown_event(self):
        """
        Create a update message
        """
        return K8sPodUpdateMessage(sender_name='test_k8s_processor_unknown',
                                   event='Unknown Event',
                                   namespace='test_k8s_processor_namespace',
                                   pod='test_k8s_processor_pod')

    @pytest.fixture
    def init_multiprocess_metadata_cache_with_data(self, started_actor, update_metadata_cache_message_added_event,
                                                   dummy_pipe_out):
        """
        Initialize the metadata cache of the actor
        """
        started_actor.send_data(update_metadata_cache_message_added_event)
        _ = recv_from_pipe(dummy_pipe_out, 2)
        return started_actor

    @pytest.fixture()
    def hwpc_report(self, update_metadata_cache_message_added_event):
        """
        Return a HWPC Report
        """
        json_input = extract_rapl_reports_with_2_sockets(1)[0]
        report = HWPCReport.from_json(json_input)
        report.target = update_metadata_cache_message_added_event.containers_id[0]

        return report

    @pytest.fixture()
    def hwpc_report_with_metadata(self, hwpc_report, update_metadata_cache_message_added_event):
        """
        Return a HWPC report with metadata
        """
        hwpc_report_with_metadata = deepcopy(hwpc_report)

        hwpc_report_with_metadata.metadata[POD_NAMESPACE_METADATA_KEY] = \
            update_metadata_cache_message_added_event.namespace
        hwpc_report_with_metadata.metadata[POD_NAME_METADATA_KEY] = update_metadata_cache_message_added_event.pod

        for label_name, label_value in update_metadata_cache_message_added_event.labels.items():
            hwpc_report_with_metadata.metadata[f"label_{label_name}"] = label_value

        return hwpc_report_with_metadata

    @pytest.fixture
    def report_to_be_sent(self):
        """
        This fixture must return the report class for testing
        """
        return HWPCReport

    @pytest.fixture
    def actor(self, started_fake_target_actor, pods_list, mocked_watch_initialized,
              multiprocess_metadata_cache_empty):
        with patch('kubernetes.client.CoreV1Api',
                   return_value=Mock(list_pod_for_all_namespaces=Mock(return_value=pods_list))):
            with patch('kubernetes.config.load_kube_config', return_value=Mock()):
                with patch('kubernetes.watch.Watch', return_value=mocked_watch_initialized):
                    with patch('powerapi.processor.pre.k8s.k8s_pre_processor_actor.K8sMetadataCache',
                               return_value=multiprocess_metadata_cache_empty):
                        return K8sPreProcessorActor(name='test_k8s_processor_actor', ks8_api_mode=MANUAL_CONFIG_MODE,
                                                    target_actors=[started_fake_target_actor],
                                                    level_logger=logging.DEBUG)

    def test_update_metadata_cache_with_added_event(self, started_actor, update_metadata_cache_message_added_event,
                                                    dummy_pipe_out, shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of an added event
        """
        update_message = update_metadata_cache_message_added_event
        started_actor.send_data(update_message)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result.pod_labels[(update_message.namespace, update_message.pod)] == update_message.labels
        assert result.pod_containers[(update_message.namespace, update_message.pod)] == update_message.containers_id

        for container_id in update_message.containers_id:
            assert result.containers_pod[container_id] == (update_message.namespace, update_message.pod)

    def test_update_metadata_cache_with_modified_event(self, init_multiprocess_metadata_cache_with_data,
                                                       update_metadata_cache_message_modified_event, dummy_pipe_out,
                                                       shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of a modified event
        """
        started_actor = init_multiprocess_metadata_cache_with_data

        update_message = update_metadata_cache_message_modified_event
        started_actor.send_data(update_message)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result.pod_labels[(update_message.namespace, update_message.pod)] == update_message.labels
        assert result.pod_containers[(update_message.namespace, update_message.pod)] == update_message.containers_id

        for container_id in update_message.containers_id:
            assert result.containers_pod[container_id] == (update_message.namespace, update_message.pod)

    def test_update_metadata_cache_with_deleted_event(self, init_multiprocess_metadata_cache_with_data,
                                                      update_metadata_cache_message_deleted_event, dummy_pipe_out,
                                                      shutdown_system):
        """
        Test that metadata_cache is correctly updated when a reception of a deleted event
        """
        started_actor = init_multiprocess_metadata_cache_with_data

        update_message = update_metadata_cache_message_deleted_event

        started_actor.send_data(update_message)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert len(result.pod_labels) == 0
        assert len(result.pod_containers) == 0
        assert len(result.containers_pod) == 0

    def test_update_metadata_cache_with_unknown_event_does_not_modify_it(self,
                                                                         init_multiprocess_metadata_cache_with_data,
                                                                         update_metadata_cache_message_unknown_event,
                                                                         dummy_pipe_out,
                                                                         update_metadata_cache_message_added_event,
                                                                         shutdown_system):
        """
        Test that metadata_cache is not updated when a reception of a unknown event
        """
        started_actor = init_multiprocess_metadata_cache_with_data

        update_message = update_metadata_cache_message_unknown_event
        update_message_added = update_metadata_cache_message_added_event
        started_actor.send_data(update_message)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result.pod_labels[(update_message.namespace, update_message.pod)] == update_message_added.labels
        assert result.pod_containers[(update_message.namespace, update_message.pod)] == \
               update_message_added.containers_id

        for container_id in update_message.containers_id:
            assert result.containers_pod[container_id] == (update_message_added.namespace, update_message_added.pod)

    def test_add_metadata_to_hwpc_report(self,
                                         init_multiprocess_metadata_cache_with_data,
                                         hwpc_report, hwpc_report_with_metadata,
                                         dummy_pipe_out, shutdown_system):
        """
        Test that a HWPC report is modified with the correct metadata
        """
        started_actor = init_multiprocess_metadata_cache_with_data

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result[1] == hwpc_report_with_metadata

    def test_add_metadata_to_hwpc_report_does_not_modify_report_with_unknown_container_id(self,
                                                                                          started_actor,
                                                                                          hwpc_report,
                                                                                          dummy_pipe_out,
                                                                                          shutdown_system):
        """
        Test that a HWPC report is not modified with an unknown container id
        """

        started_actor.send_data(hwpc_report)

        result = recv_from_pipe(dummy_pipe_out, 2)

        assert result[1] == hwpc_report
