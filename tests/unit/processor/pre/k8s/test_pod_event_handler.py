# Copyright (c) 2026, Inria
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

from collections.abc import Mapping
from unittest.mock import Mock

import pytest

pytest.importorskip("kubernetes")

from kubernetes.client import V1ContainerStatus, V1ObjectMeta, V1Pod, V1PodStatus

from powerapi.processor.pre.k8s.pod_event_handler import KubernetesPodEventHandler
from powerapi.utils.metadata import build_metadata_mapping


def make_container_status(
    container_id: str | None = None,
    name: str = "powerapi",
    image: str = "powerapi:pytest"
) -> V1ContainerStatus:
    """
    Build the subset of a container status used by the event handler.
    """
    status = Mock(spec=V1ContainerStatus)
    status.name = name
    status.container_id = container_id
    status.image = image
    return status


def make_pod(
    name: str = "pytest",
    namespace: str = "powerapi",
    labels: dict[str, str] | None = None,
    container_statuses: list[V1ContainerStatus] | None = None
) -> V1Pod:
    """
    Build the subset of a Pod used by the event handler.
    """
    metadata = Mock(spec=V1ObjectMeta)
    metadata.name = name
    metadata.namespace = namespace
    metadata.labels = labels

    status = Mock(spec=V1PodStatus)
    status.container_statuses = container_statuses

    return Mock(spec=V1Pod, metadata=metadata, status=status)


@pytest.fixture
def pod_event_handler(metadata_registry):
    """
    Factory fixture for creating a pod event handler.
    """

    def _create_event_handler(labels_mapping: Mapping[str, str]) -> KubernetesPodEventHandler:
        event_handler = KubernetesPodEventHandler(metadata_registry, labels_mapping)
        return event_handler

    return _create_event_handler


@pytest.mark.parametrize("event_type", ["ADDED", "MODIFIED"])
def test_event_register_containers_metadata(event_type, metadata_registry, pod_event_handler):
    """
    Valid events should populate the registry for each started container in the Pod.
    """
    containers = [
        ("1111111111111111111111111111111111111111111111111111111111111111", "first", "powerapi:first"),
        ("2222222222222222222222222222222222222222222222222222222222222222", "second", "powerapi:second"),
    ]

    event_handler = pod_event_handler(build_metadata_mapping(["app.kubernetes.io/name"], "k8s_pod_label_"))
    containers_statuses = [
        make_container_status(f'pytest://{container_id}', name, image)
        for container_id, name, image in containers
    ]
    pod = make_pod(
        labels={"app.kubernetes.io/name": "pytest", "ignored/label": "ignored"},
        container_statuses=containers_statuses
    )

    event_handler.handle(event_type, pod)

    for container_id, name, image in containers:
        assert metadata_registry.get_metadata(container_id) == {
            "k8s_pod_name": pod.metadata.name,
            "k8s_pod_namespace": pod.metadata.namespace,
            "k8s_container_name": name,
            "k8s_container_image": image,
            "k8s_pod_label_app_kubernetes_io_name": "pytest",
        }


@pytest.mark.parametrize("labels", [None, {}])
def test_event_registers_container_when_pod_has_no_labels(labels, metadata_registry, pod_event_handler):
    """
    Containers should be registered without label metadata when Pod labels are absent.
    """
    event_handler = pod_event_handler(build_metadata_mapping(["app.kubernetes.io/name"], "k8s_pod_label_"))

    container_id = "1111111111111111111111111111111111111111111111111111111111111111"
    containers_statuses = [
        make_container_status(f'pytest://{container_id}', "test", "powerapi:test"),
    ]
    pod = make_pod(labels=labels, container_statuses=containers_statuses)

    event_handler.handle("ADDED", pod)

    assert metadata_registry.get_metadata(container_id) == {
        "k8s_pod_name": "pytest",
        "k8s_pod_namespace": "powerapi",
        "k8s_container_name": "test",
        "k8s_container_image": "powerapi:test",
    }


@pytest.mark.parametrize("container_statuses", [None, []])
def test_event_accepts_pod_without_container_statuses(container_statuses, metadata_registry, pod_event_handler):
    """
    A Pod without available container statuses should not create registry entries.
    """
    metadata_registry.set_metadata = Mock(wraps=metadata_registry.set_metadata)
    event_handler = pod_event_handler({})
    pod = make_pod(container_statuses=container_statuses)

    event_handler.handle("ADDED", pod)

    metadata_registry.set_metadata.assert_not_called()


@pytest.mark.parametrize("event_type", ["ADDED", "MODIFIED"])
def test_event_ignores_containers_without_runtime_id(event_type, metadata_registry, pod_event_handler):
    """
    Containers without ID should not be added to the registry.
    """
    metadata_registry.set_metadata = Mock(wraps=metadata_registry.set_metadata)
    event_handler = pod_event_handler({})
    pod = make_pod(container_statuses=[make_container_status(None)])

    event_handler.handle(event_type, pod)

    metadata_registry.set_metadata.assert_not_called()


def test_deleted_event_retains_metadata(metadata_registry, pod_event_handler):
    """
    Deleted Pod events deliberately leave existing registry entries intact.
    """
    metadata_registry.set_metadata = Mock(wraps=metadata_registry.set_metadata)
    event_handler = pod_event_handler({})

    event_handler.handle("DELETED", make_pod())

    metadata_registry.set_metadata.assert_not_called()


def test_unexpected_event_raises_value_error(metadata_registry, pod_event_handler):
    """
    Unsupported Kubernetes event types should be rejected.
    """
    event_handler = pod_event_handler({})

    with pytest.raises(ValueError, match="Unexpected Kubernetes pod event: PYTEST"):
        event_handler.handle("PYTEST", make_pod())
