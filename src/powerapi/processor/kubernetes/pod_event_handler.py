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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .metadata_registry import KubernetesMetadataRegistry

if TYPE_CHECKING:
    from kubernetes.client import V1ContainerStatus, V1Pod


class KubernetesPodEventHandler:
    """
    Translates Kubernetes pod events into metadata registry operations.
    """

    def __init__(self, metadata_registry: KubernetesMetadataRegistry, labels_mapping: Mapping[str, str]):
        """
        Initialize the Kubernetes pod event handler.
        :param metadata_registry: Registry containing metadata
        :param labels_mapping: Mapping from Kubernetes pod label names to canonical report metadata names
        """
        self.metadata_registry = metadata_registry
        self.label_mapping = labels_mapping

    def handle(self, event_type: str, pod: V1Pod) -> None:
        """
        Apply a Kubernetes pod event to the metadata registry.
        :param event_type: Kubernetes pod event type
        :param pod: Pod associated with the event
        :raises ValueError: If the event type is unsupported
        """
        match event_type:
            case 'ADDED' | 'MODIFIED':
                self._set_pod_metadata(pod)
            case 'DELETED':
                # Retain metadata so reports already in the pipeline can still be enriched.
                return
            case _:
                raise ValueError(f'Unexpected Kubernetes pod event: {event_type}')

    @staticmethod
    def _extract_container_id(container_status: V1ContainerStatus) -> str:
        """
        Extract the runtime-specific ID from a Kubernetes container status.
        :param container_status: Container status from which to extract the ID
        :return: Container ID without its runtime prefix
        """
        return container_status.container_id.partition('://')[2]

    def _build_pod_metadata(self, pod: V1Pod) -> dict[str, str]:
        """
        Build the report metadata shared by all containers of a pod.
        :param pod: Pod from which to build metadata
        :return: Mapping of the metadata shared by the pod containers
        """
        metadata = {
            'k8s_pod_name': pod.metadata.name,
            'k8s_pod_namespace': pod.metadata.namespace,
        }

        if pod.metadata.labels:
            for source_name, canonical_name in self.label_mapping.items():
                if source_name in pod.metadata.labels:
                    metadata[canonical_name] = pod.metadata.labels[source_name]

        return metadata

    def _set_pod_metadata(self, pod: V1Pod) -> None:
        """
        Register metadata for every started container of a pod.
        Container statuses without a valid runtime ID are ignored.
        :param pod: Pod whose container metadata should be registered
        """
        pod_metadata = self._build_pod_metadata(pod)

        if pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                if container_status.container_id is None:
                    continue

                container_id = self._extract_container_id(container_status)

                container_metadata = pod_metadata.copy()
                container_metadata['k8s_container_name'] = container_status.name
                container_metadata['k8s_container_image'] = container_status.image

                self.metadata_registry.set_metadata(container_id, container_metadata)
