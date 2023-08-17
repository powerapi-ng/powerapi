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

# pylint: disable=W0603,W0718

import logging
from logging import Logger
from time import sleep

from kubernetes import client, config, watch
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException

from powerapi.actor import State, Actor
from powerapi.message import StartMessage, PoisonPillMessage, K8sPodUpdateMessage
from powerapi.processor.k8s.k8s_monitor_handlers import K8sMonitorAgentStartMessageHandler, \
    K8sMonitorAgentPoisonPillMessageHandler

LOCAL_CONFIG_MODE = "local"
MANUAL_CONFIG_MODE = "manual"
CLUSTER_CONFIG_MODE = "cluster"

ADDED_EVENT = 'ADDED'
DELETED_EVENT = 'DELETED'
MODIFIED_EVENT = 'MODIFIED'

v1_api = None


def local_config():
    """
    Return local kubectl
    """
    config.load_kube_config()


def manual_config():
    """
    Return the manual configuration
    """
    # Manual config
    configuration = client.Configuration()
    # Configure API key authorization: BearerToken
    configuration.api_key["authorization"] = "YOUR_API_KEY"
    # Defining host is optional and default to http://localhost
    configuration.host = "http://localhost"
    Configuration.set_default(configuration)


def cluster_config():
    """
    Return the cluster configuration
    """
    config.load_incluster_config()


def load_k8s_client_config(logger: Logger, mode: str = None):
    """
    Load K8S client configuration according to the `mode`.
    If no mode is given `LOCAL_CONFIG_MODE` is used.
    params:
        mode : one of `LOCAL_CONFIG_MODE`, `MANUAL_CONFIG_MODE`
               or `CLUSTER_CONFIG_MODE`
    """
    logger.debug("Loading k8s api conf mode %s ", mode)
    {
        LOCAL_CONFIG_MODE: local_config,
        MANUAL_CONFIG_MODE: manual_config,
        CLUSTER_CONFIG_MODE: cluster_config,
    }.get(mode, local_config)()


def get_core_v1_api(logger: Logger, mode: str = None):
    """
    Returns a handler to the k8s API.
    """
    global v1_api
    if v1_api is None:
        load_k8s_client_config(logger=logger, mode=mode)
        v1_api = client.CoreV1Api()
        logger.info(f"Core v1 api access : {v1_api}")
    return v1_api


def extract_containers(pod_obj):
    """
    Extract the containers ids from a pod
    :param pod_obj: Pod object for extracting the containers ids
    """
    if not pod_obj.status.container_statuses:
        return []

    container_ids = []
    for container_status in pod_obj.status.container_statuses:
        container_id = container_status.container_id
        if not container_id:
            continue
        # container_id actually depends on the container engine used by k8s.
        # It seems that is always start with <something>://<actual_id>
        # e.g.
        # 'containerd://2289b494f36b93647cfefc6f6ed4d7f36161d5c2f92d1f23571878a4e85282ed'
        container_id = container_id[container_id.index("//") + 2:]
        container_ids.append(container_id)

    return sorted(container_ids)


class K8sMonitorAgentState(State):
    """
    State related to a K8sMonitorAgentActor
    """

    def __init__(self, actor: Actor, time_interval: int, timeout_query: int, listener_agent: Actor, k8s_api_mode: str):
        State.__init__(self, actor=actor)
        self.time_interval = time_interval
        self.timeout_query = timeout_query
        self.listener_agent = listener_agent
        self.k8s_api_mode = k8s_api_mode
        self.active_monitoring = False
        self.monitor_thread = None


class K8sMonitorAgentActor(Actor):
    """
    An actor that monitors the k8s API and sends messages
    when pod are created, removed or modified.
    """

    def __init__(self, name: str, listener_agent: Actor, k8s_api_mode: str = None, time_interval: int = 10,
                 timeout_query=5, level_logger: int = logging.WARNING):
        """
        :param str name: The actor name
        :param K8sProcessorActor listener_agent: actor waiting for notifications of the monitor
        :param k8s_api_mode: the used k8s API mode
        :param int timeout_query: Timeout for queries
        :param int time_interval: Time interval for the monitoring
        :pram int level_logger: The logger level
        """
        Actor.__init__(self, name=name, level_logger=logging.DEBUG)
        self.state = K8sMonitorAgentState(actor=self, time_interval=time_interval, timeout_query=timeout_query,
                                          listener_agent=listener_agent, k8s_api_mode=k8s_api_mode)

    def setup(self):
        """
        Define StartMessage handler and PoisonPillMessage handler
        """
        print('setup monitor called')
        self.add_handler(message_type=StartMessage, handler=K8sMonitorAgentStartMessageHandler(state=self.state))
        self.add_handler(message_type=PoisonPillMessage,
                         handler=K8sMonitorAgentPoisonPillMessageHandler(state=self.state))

    def query_k8s(self):
        """
        Query k8s for changes and send the related information to the listener
        """
        while self.state.active_monitoring:
            try:
                self.logger.debug("Start - K8sMonitorAgentActor Querying k8s")
                events = self.k8s_streaming_query(timeout_seconds=self.state.timeout_query,
                                                  k8sapi_mode=self.state.k8s_api_mode)
                for event in events:
                    event_type, namespace, pod_name, container_ids, labels = event
                    self.state.listener_agent.send_data(
                        K8sPodUpdateMessage(
                            sender_name=self.name,
                            event=event_type,
                            namespace=namespace,
                            pod=pod_name,
                            containers_id=container_ids,
                            labels=labels
                        )
                    )
                sleep(self.state.time_interval)
            except Exception as ex:
                self.logger.warning(ex)
                self.logger.warning("Failed streaming query %s", ex)

    def k8s_streaming_query(self, timeout_seconds: int, k8sapi_mode: str) -> list:
        """
        Return a list of events by using the provided paremeters
        :param int timeout_seconds: Timeout in seconds for waiting for events
        :param str k8sapi_mode: Kind of API mode
        """
        api = get_core_v1_api(mode=k8sapi_mode, logger=self.logger)
        events = []
        w = watch.Watch()

        try:
            for event in w.stream(
                    api.list_pod_for_all_namespaces, timeout_seconds
            ):

                if not event["type"] in {DELETED_EVENT, ADDED_EVENT, MODIFIED_EVENT}:
                    self.logger.warning(
                        "UNKNOWN EVENT TYPE : %s :  %s  %s",
                        event['type'], event['object'].metadata.name, event
                    )
                    continue
                pod_obj = event["object"]
                namespace, pod_name = \
                    pod_obj.metadata.namespace, pod_obj.metadata.name
                container_ids = (
                    [] if event["type"] == "DELETED"
                    else extract_containers(pod_obj)
                )
                labels = pod_obj.metadata.labels
                events.append(
                    (event["type"], namespace, pod_name, container_ids, labels)
                )

        except ApiException as ae:
            self.logger.error("APIException %s %s", ae.status, ae)
        except Exception as undef_e:
            self.logger.error("Error when watching Exception %s %s", undef_e, event)
        return events
