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

from powerapi.actor import State
from powerapi.handler import StartHandler, PoisonPillMessageHandler
from powerapi.message import Message
from powerapi.processor.handlers import ProcessorReportHandler

POD_NAMESPACE_METADATA_KEY = 'pod_namespace'
POD_NAME_METADATA_KEY = 'pod_name'


class K8sPreProcessorActorStartMessageHandler(StartHandler):
    """
    Start the K8sProcessorActor
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state=state)

    #
    def initialization(self):
        for actor in self.state.target_actors:
            actor.connect_data()


class K8sPreProcessorActorHWPCReportHandler(ProcessorReportHandler):
    """
    Process the HWPC Reports
    """

    def __init__(self, state: State):
        ProcessorReportHandler.__init__(self, state=state)

    def handle(self, message: Message):

        # Add pod name, namespace and labels to the report
        c_id = clean_up_container_id(message.target)

        namespace, pod = self.state.metadata_cache_manager.get_container_pod(c_id)
        if namespace is None or pod is None:
            self.state.actor.logger.warning(
                f"Container with no associated pod : {message.target}, {c_id}, {namespace}, {pod}"
            )
            namespace = ""
            pod = ""
        else:
            self.state.actor.logger.debug(
                f"K8sPreProcessorActorHWPCReportHandler add metadata to report {c_id}, {namespace}, {pod}"
            )

            labels = self.state.metadata_cache_manager.get_pod_labels(namespace, pod)
            for label_key, label_value in labels.items():
                message.metadata[f"label_{label_key}"] = label_value

        message.metadata[POD_NAMESPACE_METADATA_KEY] = namespace
        message.metadata[POD_NAME_METADATA_KEY] = pod

        self._send_report(report=message)


class K8sPreProcessorActorPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
     Stop the K8sProcessorActor
     """

    def __init__(self, state: State):
        PoisonPillMessageHandler.__init__(self, state=state)

    def teardown(self, soft=False):
        for actor in self.state.target_actors:
            actor.close()


def clean_up_container_id(c_id):
    """
    On some system, we receive a container id that requires some cleanup to match
    the id returned by the k8s api
    k8s creates cgroup directories, which is what we get as id from the sensor,
    according to this pattern:
         /kubepods/<qos>/pod<pod-id>/<containerId>
    depending on the container engine, we need to clean up the <containerId> part
    """

    if "/docker-" in c_id:
        # for path like :
        # /kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod435532e3_546d_45e2_8862_d3c7b320d2d9.slice/
        # docker-68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a.scope
        # where we actually only want the end of that path :
        # 68aa4b590997e0e81257ac4a4543d5b278d70b4c279b4615605bb48812c9944a
        try:
            return c_id[c_id.rindex("/docker-") + 8: -6]
        except ValueError:
            return c_id
    else:
        # /kubepods/besteffort/pod42006d2c-cad7-4575-bfa3-91848a558743/ba28184d18d3fc143d5878c7adbefd7d1651db70ca2787f40385907d3304e7f5
        try:
            return c_id[c_id.rindex("/") + 1:]
        except ValueError:
            return c_id
