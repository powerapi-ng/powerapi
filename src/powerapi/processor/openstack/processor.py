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

from collections.abc import Iterable
from multiprocessing import Manager
from typing import Any

from powerapi.processor.processor import Processor, ReportProcessor
from powerapi.report import HWPCReport

from ._utils import get_instance_name_from_libvirt_cgroup
from .metadata_registry import OpenStackMetadataRegistry
from .monitor_agent import OpenStackMonitorAgent, OpenStackMonitorConfig


class OpenStackProcessor(Processor):
    """
    Manage OpenStack metadata resources for report processors.
    """
    metadata_registry: OpenStackMetadataRegistry

    def __init__(self, monitor_config: OpenStackMonitorConfig):
        """
        Create a new OpenStack processor.
        :param monitor_config: Configuration of the monitoring agent
        """
        self.monitor_config = monitor_config

        self.manager = None
        self.monitor_agent = None

    def initialize(self) -> None:
        """
        Initialize shared metadata resources and start OpenStack API monitoring.
        :raises RuntimeError: If the processor is already initialized
        """
        if self.manager is not None:
            raise RuntimeError('Processor already initialized')

        try:
            self.manager = Manager()
            self.metadata_registry = OpenStackMetadataRegistry(self.manager)
            self.monitor_agent = OpenStackMonitorAgent(self.metadata_registry, self.monitor_config)
            self.monitor_agent.start()
        except BaseException:
            self.teardown()
            raise

    def get_report_processors(self) -> Iterable[ReportProcessor[Any]]:
        """
        Return initialized report processors for all supported report types.
        :return: Iterable of initialized report processors
        """
        return (
            HWPCReportProcessor(self.metadata_registry),
        )

    def teardown(self) -> None:
        """
        Clean up resources allocated during initialization.
        """
        try:
            if self.monitor_agent is not None:
                if self.monitor_agent.pid is not None:
                    self.monitor_agent.terminate()
                    self.monitor_agent.join()
                self.monitor_agent = None
        finally:
            if self.manager is not None:
                self.manager.shutdown()
                self.manager = None


class HWPCReportProcessor(ReportProcessor[HWPCReport]):
    """
    Enrich or filter HWPC reports using cached OpenStack metadata.
    """

    def __init__(self, metadata_registry: OpenStackMetadataRegistry):
        """
        Initialize a report processor for HWPC reports.
        :param metadata_registry: Shared platform metadata registry
        """
        super().__init__(HWPCReport)

        self.metadata_registry = metadata_registry

    def process(self, report: HWPCReport) -> HWPCReport | None:
        """
        Enrich matching reports in place with cached OpenStack metadata.
        Cached values overwrite existing metadata keys.
        Non-OpenStack targets pass through unchanged; matching reports without cached metadata are dropped.
        :param report: Incoming HWPC report
        :return: The report, possibly modified, or None if dropped
        """
        instance_name = get_instance_name_from_libvirt_cgroup(report.target)
        if instance_name is not None:
            server_metadata = self.metadata_registry.get_metadata(report.sensor, instance_name)
            if server_metadata is None:
                # Drop the report if the server metadata is not present in the registry.
                return None

            report.metadata.update(server_metadata)

        return report
