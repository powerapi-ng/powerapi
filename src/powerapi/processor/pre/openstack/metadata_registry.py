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

from collections.abc import MutableMapping
from multiprocessing.managers import SyncManager


class OpenStackMetadataRegistry:
    """
    OpenStack metadata registry.
    """

    def __init__(self, manager: SyncManager):
        """
        :param manager: Manager of the shared metadata registry
        """
        self._server_metadata: MutableMapping[tuple[str, str], dict[str, str]] = manager.dict()

    def set_metadata(self, host: str, instance_name: str, metadata: dict[str, str]) -> None:
        """
        Set metadata for the given OpenStack server.
        :param host: Name of the host running the server
        :param instance_name: Internal instance name of the server
        :param metadata: Metadata entry
        """
        self._server_metadata[(host, instance_name)] = metadata

    def get_metadata(self, host: str, instance_name: str) -> dict[str, str] | None:
        """
        Get metadata for the given OpenStack server.
        :param host: Name of the host running the server
        :param instance_name: Internal instance name of the server
        :return: Metadata entry or None if not found
        """
        return self._server_metadata.get((host, instance_name))
