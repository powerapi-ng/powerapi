# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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

from dataclasses import dataclass
from multiprocessing import Manager

ADDED_EVENT = 'ADDED'
DELETED_EVENT = 'DELETED'
MODIFIED_EVENT = 'MODIFIED'


@dataclass
class K8sContainerMetadata:
    """
    Represents a metadata cache entry for Kubernetes containers.
    """
    container_id: str
    container_name: str
    namespace: str
    pod_name: str
    pod_labels: dict


class K8sMetadataCacheManager:
    """
    Kubernetes container metadata cache manager.
    """

    def __init__(self, manager: Manager):
        """
        :param manager: Manager of the shared metadata cache
        """
        self.metadata_cache: dict[str, K8sContainerMetadata] = manager.dict()

    def update_container_metadata(self, event: str, container_metadata: K8sContainerMetadata):
        """
        Updates the metadata cache according to an event.
        :param event: Event of the metadata cache
        :param container_metadata: Container metadata entry
        """
        if event in {ADDED_EVENT, MODIFIED_EVENT}:
            self.metadata_cache[container_metadata.container_id] = container_metadata
        if event == DELETED_EVENT:
            self.metadata_cache.pop(container_metadata.container_id, None)

    def get_container_metadata(self, container_id: str) -> K8sContainerMetadata | None:
        """
        Get metadata for a specific container from the cache.
        :param container_id: Container ID (hexadecimal string of 64 characters, short format is not supported)
        :return: Container metadata entry
        """
        return self.metadata_cache.get(container_id)

    def clear_metadata_cache(self):
        """
        Clears all container metadata entries from the cache.
        """
        self.metadata_cache.clear()
