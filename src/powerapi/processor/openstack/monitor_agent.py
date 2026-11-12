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
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from multiprocessing import Event, Process
from signal import SIGINT, SIGTERM, signal

from openstack.connection import Connection
from openstack.exceptions import SDKException

from .metadata_registry import OpenStackMetadataRegistry
from .server_change_handler import OpenStackServerChangeHandler


@dataclass(frozen=True)
class OpenStackMonitorConfig:
    """
    OpenStack monitoring agent configuration.
    :param polling_interval: Interval in seconds between OpenStack API synchronizations.
    :param metadata_mapping: Mapping from OpenStack server metadata names to canonical report metadata names.
    """
    polling_interval: float
    metadata_mapping: Mapping[str, str]


class OpenStackMonitorAgent(Process):
    """
    Background monitoring agent that updates the shared metadata cache from the OpenStack API.
    It requires credentials with sufficient permissions to access server metadata across all projects.
    Permission to read Nova Extended Server Attributes (OS-EXT-SRV-ATTR) is **mandatory** in order to map cgroups to servers.
    """

    def __init__(self, registry: OpenStackMetadataRegistry, config: OpenStackMonitorConfig, level_logger: int = logging.WARNING):
        """
        :param registry: OpenStack metadata registry
        :param config: Configuration of the monitor agent
        :param level_logger: Logger level
        """
        super().__init__(name='openstack-processor-monitor-agent')

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter('%(asctime)s || %(levelname)s || %(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.config = config
        self.server_change_handler = OpenStackServerChangeHandler(registry, config.metadata_mapping)

        self._stop_monitoring = Event()

    @staticmethod
    def _setup_openstack_api_client() -> Connection:
        """
        Setup OpenStack API client.
        Configuration is taken from OS_* environment variables.
        """
        return Connection(app_name='PowerAPI')

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for the current Process.
        """
        def stop_monitor(_, __):
            self._stop_monitoring.set()
            sys.exit(0)

        signal(SIGTERM, stop_monitor)
        signal(SIGINT, stop_monitor)

    def run(self) -> None:
        """
        Main code executed by the OpenStack monitor agent.
        """
        self._setup_signal_handlers()

        api_client = self._setup_openstack_api_client()
        changes_since = None

        while not self._stop_monitoring.is_set():
            try:
                changes_since = self.fetch_server_changes(api_client, changes_since)
            except SDKException as exn:
                logging.warning('Failed to retrieve server changes from OpenStack API: %s', exn)
            except (AttributeError, ValueError) as exn:
                logging.error('Required server attribute is missing from the OpenStack API response: %s', exn)

            if self._stop_monitoring.wait(self.config.polling_interval):
                break

    def fetch_server_changes(self, openstack_api: Connection, changes_since: str | None = None) -> str:
        """
        Fetch and handle OpenStack server changes.
        When no synchronization timestamp is provided, all servers are fetched.
        :param openstack_api: OpenStack API client
        :param changes_since: ISO 8601 timestamp of the previous synchronization
        :return: ISO 8601 timestamp to use for the next synchronization
        """
        next_changes_since = datetime.now(UTC).isoformat(timespec='seconds')
        query = {} if changes_since is None else {'changes_since': changes_since}

        for server in openstack_api.compute.servers(details=True, all_projects=True, **query):
            self.server_change_handler.handle(server)

        return next_changes_since
