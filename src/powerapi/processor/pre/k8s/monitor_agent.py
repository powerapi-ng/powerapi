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

import logging
import sys
from dataclasses import dataclass
from multiprocessing import Process, Event
from signal import signal, SIGTERM, SIGINT
from time import sleep

from kubernetes import client, config, watch
from kubernetes.client import V1Pod, V1PodList, V1ContainerStatus
from kubernetes.client.rest import ApiException
from urllib3.exceptions import ProtocolError

from .metadata_cache_manager import K8sMetadataCacheManager, K8sContainerMetadata, ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT

K8S_MONITOR_RETRY_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class K8sMonitorConfig:
    """
    Kubernetes monitoring agent configuration.
    :param api_mode: Kubernetes API mode (manual, local, cluster)
    :param api_host: Kubernetes API host to connect to
    :param api_key: Kubernetes API key (Bearer Token) to authenticate with
    """
    api_mode: str
    api_host: str | None = None
    api_key: str | None = None


def load_manual_k8s_config(configuration: client.Configuration, api_host: str | None, api_key: str | None) -> None:
    """
    Setup Kubernetes API client configuration manually.
    This method only supports authentication by Bearer Token.
    :param configuration: Kubernetes API client configuration
    :param api_host: The Kubernetes API host
    :param api_key: The Kubernetes API key (Bearer Token)
    """
    if not api_host:
        raise ValueError('Kubernetes API host is not defined')

    if not api_key:
        raise ValueError('Kubernetes API key is not defined')

    configuration.host = api_host
    configuration.api_key['authorization'] = api_key
    configuration.api_key_prefix['authorization'] = 'Bearer'


def build_k8s_api_client_configuration(api_mode: str, api_host: str | None, api_key: str | None) -> client.Configuration:
    """
    Build a Kubernetes API client configuration.
    :param api_mode: The Kubernetes API mode (manual, local, cluster)
    :param api_host: The Kubernetes API host
    :param api_key: The Kubernetes API key (Bearer Token)
    :return: Kubernetes API client configuration
    """
    configuration = client.Configuration()
    match api_mode.casefold():
        case 'local':
            # Setup Kubernetes API client with a kube-config file. (from KUBECONFIG environment variable, or ~/.kube/config)
            config.load_kube_config(client_configuration=configuration)
        case 'cluster':
            # Setup Kubernetes API client with the pod service account. (requires PowerAPI to be running in a pod)
            config.load_incluster_config(client_configuration=configuration)
        case 'manual':
            load_manual_k8s_config(configuration, api_host, api_key)
        case _:
            raise ValueError(f'Invalid Kubernetes API mode: {api_mode}')

    return configuration


class K8sMonitorAgent(Process):
    """
    Background monitoring agent that update the shared metadata cache from Kubernetes API events.
    """

    def __init__(self, cache_manager: K8sMetadataCacheManager, conf: K8sMonitorConfig, level_logger: int = logging.WARNING):
        """
        :param K8sMetadataCacheManager cache_manager: Metadata cache manager
        :param conf: Configuration of the k8s processor actor
        :param int level_logger: The logger level
        """
        super().__init__(name='k8s-processor-monitor-agent')

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter('%(asctime)s || %(levelname)s || ' + '%(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.metadata_cache_manager = cache_manager

        self._api_config = build_k8s_api_client_configuration(conf.api_mode, conf.api_host, conf.api_key)
        self._stop_monitoring = Event()

    @staticmethod
    def build_k8s_api_client(api_config: client.Configuration) -> client.CoreV1Api:
        """
        Build a Kubernetes API client with the given configuration.
        :param api_config: Kubernetes API configuration
        :return: Kubernetes API client
        """
        api_client = client.ApiClient(configuration=api_config)
        return client.CoreV1Api(api_client)

    def _setup_signal_handlers(self):
        """
        Setup signal handlers for the current Process.
        """
        def stop_monitor(_, __):
            self._stop_monitoring.set()
            sys.exit(0)

        signal(SIGTERM, stop_monitor)
        signal(SIGINT, stop_monitor)

    def run(self):
        """
        Main code executed by the Kubernetes monitor agent.
        """
        self._setup_signal_handlers()

        self.metadata_cache_manager.clear_metadata_cache()  # Prevents orphaned cache entries.

        api_client = self.build_k8s_api_client(self._api_config)
        while not self._stop_monitoring.is_set():
            resource_id = self.fetch_list_all_pod_for_all_namespaces(api_client)
            self.watch_list_pod_for_all_namespaces(api_client, resource_id)
            sleep(K8S_MONITOR_RETRY_DELAY_SECONDS)

    @staticmethod
    def get_containers_id_name_from_statuses(container_statuses: list[V1ContainerStatus]) -> dict[str, str]:
        """
        Extract containers ID and name from the statuses.
        :param container_statuses: List of container statuses
        :return: Dictionary mapping the containers ID to their name
        """
        return {
            container_status.container_id.split('://')[1]: container_status.name
            for container_status in container_statuses or [] if container_status.container_id is not None
        }

    def build_metadata_cache_entries_from_pod(self, pod: V1Pod) -> list[K8sContainerMetadata]:
        """
        Build and return metadata cache entries from a Kubernetes pod object.
        :param pod: Kubernetes pod
        :return: List of metadata cache entries
        """
        pod_name = pod.metadata.name
        pod_labels = pod.metadata.labels
        namespace = pod.metadata.namespace
        container_statuses = pod.status.container_statuses
        return [
            K8sContainerMetadata(container_id, container_name, namespace, pod_name, pod_labels)
            for container_id, container_name in self.get_containers_id_name_from_statuses(container_statuses).items()
        ]

    def fetch_list_all_pod_for_all_namespaces(self, api_client: client.CoreV1Api) -> int | None:
        """
        Fetch all pod for all namespaces and populate the metadata cache.
        :param api_client: Kubernetes api client
        :return: Resource version of the last fetched entry
        """
        resource_version = None
        try:
            pods: V1PodList = api_client.list_pod_for_all_namespaces(watch=False)
            resource_version = pods.metadata.resource_version
            for pod in pods.items:
                for entry in self.build_metadata_cache_entries_from_pod(pod):
                    self.metadata_cache_manager.update_container_metadata(ADDED_EVENT, entry)

        except ApiException as e:
            logging.warning('API exception caught in fetch: %s %s', e.status, e.reason)
        except ProtocolError as e:
            logging.warning('Protocol error caught in fetch: %s', e)

        return resource_version

    def watch_list_pod_for_all_namespaces(self, api_client: client.CoreV1Api, resource_version: int | None = None):
        """
        Watch k8s pods events for all namespaces and update the local metadata cache accordingly.
        :param api_client: Kubernetes API client
        :param resource_version: Resource version from where the watcher begin
        """
        try:
            w = watch.Watch()
            for event in w.stream(api_client.list_pod_for_all_namespaces, resource_version=resource_version):
                event_type = event["type"]
                if event_type not in {ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT}:
                    logging.warning('Unexpected pod event: %s', event_type)
                    continue

                for entry in self.build_metadata_cache_entries_from_pod(event["object"]):
                    self.metadata_cache_manager.update_container_metadata(event_type, entry)

            w.stop()

        except ApiException as e:
            logging.warning('API exception caught in watcher: %s %s', e.status, e.reason)
        except ProtocolError as e:
            logging.warning('Protocol error caught in watcher: %s', e)
