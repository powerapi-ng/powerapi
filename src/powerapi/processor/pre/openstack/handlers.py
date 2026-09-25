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

from powerapi.processor.handlers import ProcessorReportHandler
from powerapi.report import HWPCReport
from ._utils import get_instance_name_from_libvirt_cgroup


class HWPCReportHandler(ProcessorReportHandler[HWPCReport]):
    """
    Generic report handler for the OpenStack processor actor.
    Used to add the server metadata (from the OpenStack API) to the processed report.
    """

    def handle(self, msg: HWPCReport):
        """
        Process an HWPCReport to add the OpenStack metadata.
        :param msg: The HWPCReport to process
        """
        instance_name = get_instance_name_from_libvirt_cgroup(msg.target)
        if instance_name is not None:
            server_metadata = self.state.metadata_registry.get_metadata(msg.sensor, instance_name)
            if server_metadata is None:
                # Drop the report if the server metadata is not present in the registry.
                return

            msg.metadata.update(server_metadata)

        self._send_report(msg)
