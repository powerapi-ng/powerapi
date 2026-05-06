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

import logging
import sys
from multiprocessing import Process
from signal import signal, SIGINT, SIGTERM
from time import sleep

from openstack.compute.v2.server import Server
from openstack.connection import Connection
from openstack.exceptions import SDKException

from .metadata_cache_manager import OpenStackMetadataCacheManager, ServerMetadata


class OpenStackMonitorAgent(Process):
    """
    Background monitoring agent that updates the shared metadata cache from the OpenStack API.
    It requires credentials with sufficient permissions to access server metadata across all projects.
    Permission to read Nova Extended Server Attributes (OS-EXT-SRV-ATTR) is **mandatory** in order to map cgroups to servers.
    """

    def __init__(self, cache_manager: OpenStackMetadataCacheManager, poll_interval: float, level_logger: int = logging.WARNING):
        """
        :param cache_manager: Metadata cache manager
        :param poll_interval: Interval in seconds between OpenStack API synchronizations
        :param level_logger: Logger level
        """
        super().__init__(name='openstack-processor-monitor-agent')

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter('%(asctime)s || %(levelname)s || %(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.metadata_cache_manager = cache_manager
        self.poll_interval = poll_interval
        self.stop_monitoring = False

    @staticmethod
    def _setup_openstack_api_client() -> Connection:
        """
        Setup OpenStack API client.
        Configuration is taken from OS_* environment variables.
        """
        return Connection(app_name='PowerAPI')

    def _setup_signal_handlers(self):
        """
        Setup signal handlers for the current Process.
        """
        def stop_monitor(_, __):
            self.stop_monitoring = True
            sys.exit(0)

        signal(SIGTERM, stop_monitor)
        signal(SIGINT, stop_monitor)

    def run(self):
        """
        Main code executed by the OpenStack monitor agent.
        """
        self._setup_signal_handlers()
        openstack_api = self._setup_openstack_api_client()

        # Prevents orphaned entries that no longer exist in the OpenStack API.
        self.metadata_cache_manager.clear_metadata_cache()

        while not self.stop_monitoring:
            for server in self.fetch_servers_metadata(openstack_api):
                self.metadata_cache_manager.update_server_metadata(server)

            sleep(self.poll_interval)

    @staticmethod
    def build_metadata_cache_entry_from_server(server: Server) -> ServerMetadata:
        """
        Build and return a metadata cache entry from an OpenStack server object.
        :param server: OpenStack server object
        :return: Cache key and server metadata entry
        """
        return ServerMetadata(server.id, server.name, server.host, server.instance_name, server.metadata)

    def fetch_servers_metadata(self, openstack_api: Connection) -> list[ServerMetadata]:
        """
        Fetch servers metadata from the OpenStack API.
        :param openstack_api: OpenStack API client
        :return: List of servers metadata
        """
        try:
            return [
                self.build_metadata_cache_entry_from_server(server)
                for server in openstack_api.compute.servers(details=True, all_projects=True)
            ]
        except SDKException as exn:
            logging.warning('Failed to retrieve server metadata from OpenStack API: %s', exn.message)
        except (AttributeError, ValueError) as exn:
            logging.error('Required server attribute is missing from the OpenStack API response: %s', exn)

        return []
