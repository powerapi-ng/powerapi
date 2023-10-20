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

"""
This module provides two k8s specific actors
* `K8sProcessorActor`, which add k8s metadata to reports and forward them to another actor.
* `K8sMonitorAgent`, which monitors the k8s API and sends messages when pod are created, removed or modified.
"""
import logging

from typing import Tuple, Dict

from powerapi.actor import Actor
from powerapi.message import K8sPodUpdateMessage, StartMessage, PoisonPillMessage
from powerapi.processor.pre.k8s.k8s_monitor_actor import ADDED_EVENT, DELETED_EVENT, MODIFIED_EVENT
from powerapi.processor.pre.k8s.k8s_pre_processor_handlers import K8sPreProcessorActorHWPCReportHandler, \
    K8sPreProcessorActorK8sPodUpdateMessageHandler, K8sPreProcessorActorStartMessageHandler, \
    K8sPreProcessorActorPoisonPillMessageHandler
from powerapi.processor.processor_actor import ProcessorState, ProcessorActor
from powerapi.report import HWPCReport

DEFAULT_K8S_CACHE_NAME = 'k8s_cache'
DEFAULT_K8S_MONITOR_NAME = 'k8s_monitor'

TIME_INTERVAL_DEFAULT_VALUE = 0
TIMEOUT_QUERY_DEFAULT_VALUE = 5


class K8sMetadataCache:
    """
    K8sMetadataCache maintains a cache of pods' metadata
    (namespace, labels and id of associated containers)
    """

    def __init__(self, name: str = DEFAULT_K8S_CACHE_NAME, level_logger: int = logging.WARNING):

        self.pod_labels = {}  # (ns, pod) => [labels]
        self.containers_pod = {}  # container_id => (ns, pod)
        self.pod_containers = {}  # (ns, pod) => [container_ids]

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level_logger)

    def update_cache(self, message: K8sPodUpdateMessage):
        """
        Update the local cache for pods.

        Register this function as a callback for K8sMonitorAgent messages.
        """
        if message.event == ADDED_EVENT:
            self.pod_labels[(message.namespace, message.pod)] = message.labels
            self.pod_containers[
                (message.namespace, message.pod)
            ] = message.containers_id
            for container_id in message.containers_id:
                self.containers_pod[container_id] = \
                    (message.namespace, message.pod)

        elif message.event == DELETED_EVENT:
            self.pod_labels.pop((message.namespace, message.pod), None)
            for container_id in self.pod_containers.pop(
                    (message.namespace, message.pod), []
            ):
                self.containers_pod.pop(container_id, None)
            # logger.debug("Pod removed %s %s", message.namespace, message.pod)

        elif message.event == MODIFIED_EVENT:
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

        else:
            self.logger.error("Error : unknown event type %s ", message.event)

    def get_container_pod(self, container_id: str) -> Tuple[str, str]:
        """
        Get the pod for a container_id.

        :param str container_id: Id of the container
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

        :param str namespace: The namespace related to the pod
        :param str pod_name: The name of the pod
        :return a dict {label_name, label_value}
        """
        return self.pod_labels.get((namespace, pod_name), dict)


class K8sPreProcessorState(ProcessorState):
    """
    State related to a K8SProcessorActor
    """

    def __init__(self, actor: Actor, metadata_cache: K8sMetadataCache, target_actors: list, target_actors_names: list,
                 k8s_api_mode: str, time_interval: int, timeout_query: int, api_key: str, host: str):
        ProcessorState.__init__(self, actor=actor, target_actors=target_actors, target_actors_names=target_actors_names)
        self.metadata_cache = metadata_cache
        self.k8s_api_mode = k8s_api_mode
        self.time_interval = time_interval
        self.timeout_query = timeout_query
        self.api_key = api_key
        self.host = host


class K8sPreProcessorActor(ProcessorActor):
    """
    Pre-processor Actor that modifies reports by adding K8s related metadata
    """

    def __init__(self, name: str, ks8_api_mode: str, target_actors: list = None, target_actors_names: list = None,
                 level_logger: int = logging.WARNING,
                 timeout: int = 5000, time_interval: int = TIME_INTERVAL_DEFAULT_VALUE,
                 timeout_query: int = TIMEOUT_QUERY_DEFAULT_VALUE, api_key: str = None, host: str = None):
        ProcessorActor.__init__(self, name=name, level_logger=level_logger,
                                timeout=timeout)

        self.state = K8sPreProcessorState(actor=self, metadata_cache=K8sMetadataCache(level_logger=level_logger),
                                          target_actors=target_actors,
                                          k8s_api_mode=ks8_api_mode, time_interval=time_interval,
                                          timeout_query=timeout_query, target_actors_names=target_actors_names,
                                          api_key=api_key, host=host)

    def setup(self):
        """
        Define HWPCReportMessage handler, StartMessage handler and PoisonPillMessage Handler
        """
        ProcessorActor.setup(self)
        self.add_handler(message_type=StartMessage, handler=K8sPreProcessorActorStartMessageHandler(state=self.state))
        self.add_handler(message_type=HWPCReport, handler=K8sPreProcessorActorHWPCReportHandler(state=self.state))
        self.add_handler(message_type=PoisonPillMessage,
                         handler=K8sPreProcessorActorPoisonPillMessageHandler(state=self.state))
        self.add_handler(message_type=K8sPodUpdateMessage,
                         handler=K8sPreProcessorActorK8sPodUpdateMessageHandler(state=self.state))
