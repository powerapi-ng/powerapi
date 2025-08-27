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

from dataclasses import dataclass

from openstack.connection import Connection
from openstack.exceptions import SDKException


class MetadataSyncFailed(Exception):
    """
    Exception raised when the metadata cache sync operation fails.
    """


@dataclass(frozen=True, slots=True)
class ServerMetadata:
    """
    Represents an OpenStack server metadata cache entry.
    """
    server_id: str
    server_name: str
    host: str
    metadata: dict[str, str]


class OpenStackMetadataCacheManager:
    """
    OpenStack metadata cache manager.
    Use the OpenStack API to fetch details about the servers hosted on the infrastructure.
    It requires credentials with sufficient permissions to access server metadata across all projects.
    Permission to read Nova Extended Server Attributes (OS-EXT-SRV-ATTR) is **mandatory** in order to map cgroups to servers.
    """

    def __init__(self):
        self._openstack_api = Connection(app_name='PowerAPI')  # Configuration is taken from OS_* environment variables
        self._metadata_cache: dict[tuple, ServerMetadata] = {}

    def get_server_metadata(self, host: str, instance_name: str) -> ServerMetadata | None:
        """
        Get metadata for the server of the specified host from the cache.
        :param host: Name of the host (hypervisor) where the server is located
        :param instance_name: Name of the instance (libvirt instance name)
        :return: Server metadata cache entry
        """
        return self._metadata_cache.get((host, instance_name), None)

    def sync_metadata_cache_from_api(self) -> None:
        """
        Sync the running servers metadata cache from the OpenStack API.
        """
        try:
            for server in self._openstack_api.compute.servers(details=True, all_projects=True):
                cache_entry = ServerMetadata(server.id, server.name, server.host, server.metadata)
                self._metadata_cache[(server.host, server.instance_name)] = cache_entry
        except SDKException as exn:
            raise MetadataSyncFailed('Failed to retrieve servers metadata from OpenStack API') from exn
        except ValueError as exn:
            raise MetadataSyncFailed('Required server attribute is missing from the OpenStack API response') from exn

    def clear_metadata_cache(self) -> None:
        """
        Clears all server metadata entries from the cache.
        """
        self._metadata_cache.clear()
