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

from .metadata_registry import OpenStackMetadataRegistry

if TYPE_CHECKING:
    from openstack.compute.v2.server import Server


class OpenStackServerChangeHandler:
    """
    Translates OpenStack server changes into metadata registry operations.
    """

    def __init__(self, metadata_registry: OpenStackMetadataRegistry, metadata_mapping: Mapping[str, str]):
        """
        Initialize the OpenStack server change handler.
        :param metadata_registry: Registry containing server metadata
        :param metadata_mapping: Mapping from OpenStack metadata names to canonical report metadata names
        """
        self.metadata_registry = metadata_registry
        self.metadata_mapping = metadata_mapping

    def handle(self, server: Server) -> None:
        """
        Apply an OpenStack server change to the metadata registry.
        :param server: Changed OpenStack server
        """
        if server.status == "DELETED":
            # Retain metadata so reports already in the pipeline can still be enriched.
            return

        self._set_server_metadata(server)

    def _set_server_metadata(self, server: Server) -> None:
        """
        Register metadata for an OpenStack server.
        :param server: Server whose metadata should be registered
        """
        metadata = {
            "openstack_server_name": server.name,
            "openstack_project_id": server.project_id,
            "openstack_availability_zone": server.availability_zone
        }

        for source_name, canonical_name in self.metadata_mapping.items():
            if source_name in server.metadata:
                metadata[canonical_name] = server.metadata[source_name]

        self.metadata_registry.set_metadata(server.host, server.instance_name, metadata)
