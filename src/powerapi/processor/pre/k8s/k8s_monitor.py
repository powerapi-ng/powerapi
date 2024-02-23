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

from logging import Formatter, getLogger, StreamHandler, WARNING
from multiprocessing import Manager, Process

from kubernetes import client, config, watch
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException

from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorState, K8sMetadataCacheManager, \
    K8sPodUpdateMetadata, DELETED_EVENT, ADDED_EVENT, MODIFIED_EVENT

LOCAL_CONFIG_MODE = "local"
MANUAL_CONFIG_MODE = "manual"
CLUSTER_CONFIG_MODE = "cluster"


def _setup_k8s_client_with_local_config() -> None:
    """
    Setup Kubernetes API client with a kube-config file. (from KUBECONFIG environment variable, or ~/.kube/config)
    """
    config.load_kube_config()


def _setup_k8s_client_with_cluster_config() -> None:
    """
    Setup Kubernetes API client with the pod service account. (requires PowerAPI to be running in a Kubernetes cluster)
    """
    config.load_incluster_config()


def _setup_k8s_client_with_manual_config(host: str, api_key: str) -> None:
    """
    Setup Kubernetes API client with the user provided configuration. (Bearer Token)
    :param host: Kubernetes API host url.
    :param api_key: Kubernetes API token.
    """
    configuration = client.Configuration()

    configuration.host = host or 'http://localhost'
    configuration.api_key["authorization"] = api_key

    Configuration.set_default(configuration)


def load_k8s_api_client_configuration(actor_state: K8sPreProcessorState) -> None:
    """
    Setup Kubernetes API client according to the selected mode.
    :param actor_state: Processor Actor state.
    """
    if actor_state.k8s_api_mode is MANUAL_CONFIG_MODE:
        _setup_k8s_client_with_manual_config(actor_state.host, actor_state.api_key)
        return

    if actor_state.k8s_api_mode is CLUSTER_CONFIG_MODE:
        _setup_k8s_client_with_cluster_config()
        return

    # load local configuration by default.
    _setup_k8s_client_with_local_config()


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


class K8sMonitorAgent(Process):
    """
    A monitors the k8s API and sends messages
    when pod are created, removed or modified.
    """

    def __init__(self, name: str, concerned_actor_state: K8sPreProcessorState, level_logger: int = WARNING):
        """
        :param str name: The actor name
        :param K8sPreProcessorState concerned_actor_state: state of the actor that will use the monitored information
        :pram int level_logger: The logger level
        """
        Process.__init__(self, name=name)

        #: (logging.Logger): Logger
        self.logger = getLogger(name)
        self.logger.setLevel(level_logger)
        formatter = Formatter('%(asctime)s || %(levelname)s || ' + '%(process)d %(processName)s || %(message)s')
        handler = StreamHandler()
        handler.setFormatter(formatter)

        self.concerned_actor_state = concerned_actor_state

        # Multiprocessing Manager
        self.manager = Manager()

        # Shared cache
        self.concerned_actor_state.metadata_cache_manager = K8sMetadataCacheManager(self.manager, level_logger=level_logger)

        self.stop_monitoring = self.manager.Event()
        self.stop_monitoring.clear()

        self.k8s_api = self._setup_k8s_api_client()

    def _setup_k8s_api_client(self) -> client.CoreV1Api:
        """
        Setup Kubernetes API client.
        """
        load_k8s_api_client_configuration(self.concerned_actor_state)
        return client.CoreV1Api()

    def run(self):
        """
        Main code executed by the Monitor
        """
        self.query_k8s()

    def query_k8s(self) -> None:
        """
        Query k8s for changes and update the metadata cache
        """
        try:
            while not self.stop_monitoring.is_set():
                events = self.k8s_streaming_query()
                for event in events:
                    event_type, namespace, pod_name, container_ids, labels = event
                    cache_metadata = K8sPodUpdateMetadata(event_type, namespace, pod_name, container_ids, labels)
                    self.concerned_actor_state.metadata_cache_manager.update_cache(cache_metadata)

                self.stop_monitoring.wait(timeout=self.concerned_actor_state.time_interval)

        except BrokenPipeError:
            # This error can happen when stopping the monitor process
            return
        except Exception as ex:
            self.logger.warning("Failed streaming query %s", ex)
        finally:
            self.manager.shutdown()

    def k8s_streaming_query(self) -> list:
        """
        Return a list of events by using the provided parameters.
        """
        events = []
        w = watch.Watch()
        event = None
        try:
            for event in w.stream(self.k8s_api.list_pod_for_all_namespaces, timeout_seconds=self.concerned_actor_state.timeout_query):
                if event:
                    if event["type"] not in [DELETED_EVENT, ADDED_EVENT, MODIFIED_EVENT]:
                        self.logger.warning("Unknown event type: %s for %s", event['type'], event['object'].metadata.name)
                        continue

                    pod_obj = event["object"]
                    namespace, pod_name = pod_obj.metadata.namespace, pod_obj.metadata.name
                    container_ids = ([] if event["type"] == "DELETED" else extract_containers(pod_obj))
                    labels = pod_obj.metadata.labels
                    events.append((event["type"], namespace, pod_name, container_ids, labels))

        except ApiException as ae:
            self.logger.error("APIException %s %s", ae.status, ae)
        except Exception as undef_e:
            self.logger.error("Error when watching Exception %s %s", undef_e, event)
        return events
