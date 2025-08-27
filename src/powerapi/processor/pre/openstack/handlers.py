# Copyright (c) 2023, INRIA
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

from powerapi.handler import StartHandler, PoisonPillMessageHandler as PoisonPillHandler
from powerapi.processor.handlers import ProcessorReportHandler
from powerapi.report import HWPCReport
from ._utils import get_instance_name_from_libvirt_cgroup
from .metadata_cache_manager import ServerMetadata, MetadataSyncFailed


class StartMessageHandler(StartHandler):
    """
    Start message handler for the OpenStack processor actor.
    """

    def initialization(self):
        """
        Initialize the OpenStack processor.
        """
        for actor in self.state.target_actors:
            actor.connect_data()

        self.state.monitor_agent.start()


class PoisonPillMessageHandler(PoisonPillHandler):
    """
    PoisonPill message handler for the OpenStack processor actor.
    """

    def teardown(self, soft: bool = False):
        """
        Teardown the OpenStack processor.
        """
        for actor in self.state.target_actors:
            actor.socket_interface.close()


class HWPCReportHandler(ProcessorReportHandler):
    """
    Generic report handler for the OpenStack processor actor.
    Used to add the server metadata (from the OpenStack API) to the processed report.
    """

    def try_get_server_metadata(self, sensor_name: str, instance_name: str) -> ServerMetadata | None:
        """
        Try to get the server metadata from the cache.
        :param sensor_name: Name of the sensor
        :param instance_name: Name of the instance to fetch metadata for
        :return: Server metadata entry or None if not found
        """
        server_metadata = None
        try:
            server_metadata = self.state.metadata_cache_manager.get_server_metadata(sensor_name, instance_name)
            if server_metadata is None:
                # Retry once after syncing the metadata cache.
                self.state.metadata_cache_manager.sync_metadata_cache_from_api()
                server_metadata = self.state.metadata_cache_manager.get_server_metadata(sensor_name, instance_name)
        except MetadataSyncFailed as exn:
            self.state.logger.warning(exn)

        return server_metadata

    def handle(self, msg: HWPCReport):
        """
        Process an HWPCReport to add the Kubernetes metadata.
        :param msg: The HWPCReport to process
        """
        instance_name = get_instance_name_from_libvirt_cgroup(msg.target)
        if instance_name is not None:
            server_metadata = self.try_get_server_metadata(msg.sensor, instance_name)
            if server_metadata is None:
                # Drop the report if the server metadata is not present in the cache.
                return

            msg.target = server_metadata.server_name
            msg.metadata['openstack'] = vars(server_metadata)

        self._send_report(msg)
