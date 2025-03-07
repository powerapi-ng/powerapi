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

from powerapi.handler import StartHandler, PoisonPillMessageHandler
from powerapi.processor.handlers import ProcessorReportHandler
from powerapi.report import HWPCReport
from ._utils import extract_container_id_from_k8s_cgroups_path, is_target_a_valid_k8s_cgroups_path


class K8sPreProcessorActorStartMessageHandler(StartHandler):
    """
    Start message handler for the Kubernetes processor actor.
    """

    def initialization(self):
        """
        Initialize the Kubernetes processor.
        """
        for actor in self.state.target_actors:
            actor.connect_data()

        self.state.monitor_agent.start()


class K8sPreProcessorActorHWPCReportHandler(ProcessorReportHandler):
    """
    HWPCReport message handler for the Kubernetes processor actor.
    """

    def handle(self, msg: HWPCReport):
        """
        Process an HWPCReport to add the Kubernetes metadata.
        :param msg: The HWPCReport to process
        """
        if is_target_a_valid_k8s_cgroups_path(msg.target):
            container_id = extract_container_id_from_k8s_cgroups_path(msg.target)
            container_metadata = self.state.metadata_cache_manager.get_container_metadata(container_id)

            if container_metadata is None:
                # Drop the report if the container metadata is not present in the cache.
                # This is mainly to filter out the empty pause container present for every running POD.
                return

            msg.target = container_metadata.container_name
            msg.metadata['k8s'] = vars(container_metadata)

        self._send_report(msg)


class K8sPreProcessorActorPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    Poison Pill message handler for the Kubernetes processor actor.
    """

    def teardown(self, soft: bool = False):
        """
        Teardown the Kubernetes processor.
        """
        self.state.monitor_agent.terminate()
        self.state.monitor_agent.join()

        self.state.manager.shutdown()

        for actor in self.state.target_actors:
            actor.socket_interface.close()
