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

from typing import List

from kubernetes.client import V1Pod, V1ContainerStatus, Configuration, V1ObjectMeta, V1PodStatus


def generate_k8s_config_for_tests() -> Configuration:
    """
    Generate a Kubernetes configuration for tests.
    """
    config = Configuration()
    config.client_side_validation = False  # needs to be disabled for tests
    return config


def generate_container_status(container_id, container_name) -> V1ContainerStatus:
    """
    Generate an initialized container status object.
    """
    config = generate_k8s_config_for_tests()
    status = V1ContainerStatus(container_id=container_id, name=container_name, local_vars_configuration=config)
    return status


def generate_pod(pod_name, pod_namespace, pod_labels, container_statuses: List[V1ContainerStatus]) -> V1Pod:
    """
    Generate an initialized POD object.
    """
    config = generate_k8s_config_for_tests()
    metadata = V1ObjectMeta(name=pod_name, labels=pod_labels, namespace=pod_namespace, local_vars_configuration=config)
    status = V1PodStatus(container_statuses=container_statuses, local_vars_configuration=config)
    pod = V1Pod(metadata=metadata, status=status, local_vars_configuration=config)
    return pod


def test_extract_containers_id_name_from_statuses(initialized_monitor_agent):
    """
    Test extract the containers id and name from the statuses.
    """
    cri = 'containerd'
    cid = '0000000000000000000000000000000000000000000000000000000000000000'
    container_id = f'{cri}://{cid}'
    container_name = 'test-container-name'

    status = generate_container_status(container_id, container_name)

    res = initialized_monitor_agent.get_containers_id_name_from_statuses([status])

    assert res == {cid: container_name}


def test_extract_containers_id_name_from_statuses_with_none_container_id(initialized_monitor_agent):
    """
    Test extract the containers id and name from the statuses with None container id.
    This happens when processing an event where the container is created but has not yet been started.
    """
    container_id = None
    container_name = 'test-container-name'

    status = generate_container_status(container_id, container_name)

    res = initialized_monitor_agent.get_containers_id_name_from_statuses([status])

    assert res == {}


def test_building_metadata_cache_entry_from_pod(initialized_monitor_agent):
    """
    Test building metadata cache entries from a Kubernetes POD object.
    """

    pod_name = 'test-pod'
    pod_namespace = 'powerapi'
    pod_labels = {'executor': 'pytest'}

    cri = 'containerd'
    cid = '0000000000000000000000000000000000000000000000000000000000000000'
    container_id = f'{cri}://{cid}'
    container_name = 'test-container'
    container_statuses = [generate_container_status(container_id, container_name)]

    pod = generate_pod(pod_name, pod_namespace, pod_labels, container_statuses)
    cache_entries = initialized_monitor_agent.build_metadata_cache_entries_from_pod(pod)
    assert len(cache_entries) == 1

    cache_entry = cache_entries[0]
    assert cache_entry.pod_name == pod_name
    assert cache_entry.namespace == pod_namespace
    assert cache_entry.pod_labels == pod_labels
    assert cache_entry.container_id == cid
    assert cache_entry.container_name == container_name


def test_building_metadata_cache_entry_from_pod_without_containers(initialized_monitor_agent):
    """
    Test building metadata cache entries from a Kubernetes POD object without containers.
    """
    pod_name = 'test-pod'
    pod_namespace = 'powerapi'
    pod_labels = {'executor': 'pytest'}

    container_statuses = []

    pod = generate_pod(pod_name, pod_namespace, pod_labels, container_statuses)
    cache_entries = initialized_monitor_agent.build_metadata_cache_entries_from_pod(pod)
    assert len(cache_entries) == 0
