# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
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

from collections.abc import MutableMapping
from dataclasses import dataclass
from multiprocessing.managers import SyncManager


@dataclass(frozen=True)
class ServerMetadata:
    """
    Represents an OpenStack server metadata cache entry.
    """
    server_id: str
    server_name: str
    host: str
    instance_name: str
    metadata: dict[str, str]


class OpenStackMetadataCacheManager:
    """
    OpenStack metadata cache manager.
    """

    def __init__(self, manager: SyncManager):
        """
        :param manager: Manager of the shared metadata cache
        """
        self._metadata_cache: MutableMapping[tuple[str, str], ServerMetadata] = manager.dict()

    def get_server_metadata(self, host: str, instance_name: str) -> ServerMetadata | None:
        """
        Get metadata for the server of the specified host from the cache.
        :param host: Name of the host (hypervisor) where the server is located
        :param instance_name: Name of the instance (libvirt instance name)
        :return: Server metadata cache entry or None if not found
        """
        return self._metadata_cache.get((host, instance_name), None)

    def update_server_metadata(self, server_metadata: ServerMetadata) -> None:
        """
        Add or update metadata for a server.
        :param server_metadata: Server metadata cache entry
        """
        self._metadata_cache[(server_metadata.host, server_metadata.instance_name)] = server_metadata

    def clear_metadata_cache(self) -> None:
        """
        Clears all server metadata entries from the cache.
        """
        self._metadata_cache.clear()
