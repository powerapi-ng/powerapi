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
from powerapi.actor import Actor
from powerapi.processor.processor_actor import ProcessorState


class K8sMetadataCache:
    """
    K8sMetadataCache maintains a cache of pods' metadata
    (namespace, labels and id of associated containers)
    """

    def __init__(self):
        self.pod_labels = dict()  # (ns, pod) => [labels]
        self.containers_pod = dict()  # container_id => (ns, pod)
        self.pod_containers = dict()  # (ns, pod) => [container_ids]

    def update_cache(self, message: K8sPodUpdateMessage):
        """
        Update the local cache for pods.

        Register this function as a callback for K8sMonitorAgent messages.
        """
        if message.event == "ADDED":
            self.pod_labels[(message.namespace, message.pod)] = message.labels
            self.pod_containers[
                (message.namespace, message.pod)
            ] = message.containers_id
            for container_id in message.containers_id:
                self.containers_pod[container_id] = \
                    (message.namespace, message.pod)
            # logger.debug(
            #     "Pod added  %s %s - mdt: %s",
            #     message.namespace, message.pod, message.containers_id
            # )

        elif message.event == "DELETED":
            self.pod_labels.pop((message.namespace, message.pod), None)
            for container_id in self.pod_containers.pop(
                    (message.namespace, message.pod), []
            ):
                self.containers_pod.pop(container_id, None)
            # logger.debug("Pod removed %s %s", message.namespace, message.pod)

        elif message.event == "MODIFIED":
            self.pod_labels[(message.namespace, message.pod)] = message.labels
            for prev_container_id in self.pod_containers.pop(
                    (message.namespace, message.pod), []
            ):
                self.containers_pod.pop(prev_container_id, None)
            self.pod_containers[
                (message.namespace, message.pod)
            ] = message.containers_id
            for container_id in message.containers_id:
                self.containers_pod[container_id] = \
                    (message.namespace, message.pod)

            # logger.debug(
            #     "Pod modified %s %s , mdt: %s",
            #     message.namespace, message.pod, message.containers_id
            # )
        else:
            logger.error("Error : unknown event type %s ", message.event)

    def get_container_pod(self, container_id) -> Tuple[str, str]:
        """
        Get the pod for a container_id.

        :param container_id
        :return a tuple (namespace, pod_name) of (None, None) if no pod
                could be found for this container
        """
        ns_pod = self.containers_pod.get(container_id, None)
        if ns_pod is None:
            return None, None
        return ns_pod

    def get_pod_labels(self, namespace: str, pod_name: str) -> Dict[str, str]:
        """
        Get labels for a pod.

        :param namespace
        :param
        :return a dict {label_name, label_value}
        """
        return self.pod_labels.get((namespace, pod_name), dict)


class K8sProcessorState(ProcessorState):
    """
    State related to a K8SProcessorActor
    """

    def __init__(self, actor: Actor, uri: str, regexp: str, target_actors: list):
        ProcessorState.__init__(self, actor=actor, target_actors=target_actors)
        self.regexp = re.compile(regexp)
        self.daemon_uri = None if uri == '' else uri
        print('used openReadOnly', str(type(openReadOnly)))
        self.libvirt = openReadOnly(self.daemon_uri)


class K8sProcessorActor(ProcessorActor):
    """
    Processor Actor that modifies reports by replacing libvirt id by open stak uuid
    """

    def __init__(self, name: str, uri: str, regexp: str, target_actors: list = None,
                 level_logger: int = logging.WARNING,
                 timeout: int = 5000):
        ProcessorActor.__init__(self, name=name, target_actors=target_actors, level_logger=level_logger,
                                timeout=timeout)
        self.state = LibvirtProcessorState(actor=self, uri=uri, regexp=regexp, target_actors=target_actors)

    def setup(self):
        """
        Define ReportMessage handler and StartMessage handler
        """
        ProcessorActor.setup(self)
        self.add_handler(message_type=StartMessage, handler=LibvirtProcessorStartHandler(state=self.state))
        self.add_handler(message_type=Report, handler=LibvirtProcessorReportHandler(state=self.state))
