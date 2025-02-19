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
from multiprocessing import Process
from signal import signal, SIGTERM, SIGINT

from kubernetes import client, config, watch
from kubernetes.client import V1Pod, V1PodList, V1ContainerStatus
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException
from urllib3.exceptions import ProtocolError

from .metadata_cache_manager import ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT
from .metadata_cache_manager import K8sMetadataCacheManager, K8sContainerMetadata

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


def load_k8s_api_client_configuration(api_mode: str, api_host: str, api_key: str) -> None:
    """
    Setup Kubernetes API client according to the selected mode.
    :param api_mode: API mode (manual, local, cluster)
    :param api_host: API host to connect to
    :param api_key: API key (Bearer Token) to authenticate with
    """
    if api_mode.casefold() == MANUAL_CONFIG_MODE:
        _setup_k8s_client_with_manual_config(api_host, api_key)
        return

    if api_mode.casefold() == CLUSTER_CONFIG_MODE:
        _setup_k8s_client_with_cluster_config()
        return

    # load local configuration by default.
    _setup_k8s_client_with_local_config()


class K8sMonitorAgent(Process):
    """
    Background monitoring agent that update the shared metadata cache from Kubernetes API events.
    """

    def __init__(self, cache_manager: K8sMetadataCacheManager, api_mode: str, api_host: str, api_key: str, level_logger: int = logging.WARNING):
        """
        :param K8sMetadataCacheManager cache_manager: Metadata cache manager
        :param str api_mode: The Kubernetes API mode (manual, local, cluster)
        :param str api_host: The Kubernetes API host
        :param str api_key: The Kubernetes API key (Bearer Token)
        :param int level_logger: The logger level
        """
        super().__init__(name='k8s-processor-monitor-agent')

        #: (logging.Logger): Logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter('%(asctime)s || %(levelname)s || ' + '%(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.metadata_cache_manager = cache_manager

        self.k8s_api = self._setup_k8s_api_client(api_mode, api_host, api_key)

        self.stop_monitoring = False

    @staticmethod
    def _setup_k8s_api_client(api_mode: str, api_host: str, api_key: str) -> client.CoreV1Api:
        """
        Setup Kubernetes API client.
        :param api_mode: The Kubernetes API mode (manual, local, cluster)
        :param api_host: The Kubernetes API host
        :param api_key: The Kubernetes API key (Bearer Token)
        """
        load_k8s_api_client_configuration(api_mode, api_host, api_key)
        return client.CoreV1Api()

    def _setup_signal_handlers(self):
        """
        Setup signal handlers for the current Process.
        """
        def stop_monitor(_, __):
            self.stop_monitoring = True
            sys.exit(0)

        signal(SIGTERM, stop_monitor)
        signal(SIGINT, stop_monitor)

    def run(self):
        """
        Main code executed by the Kubernetes monitor agent.
        """
        self._setup_signal_handlers()

        # Clearing the metadata cache before starting prevents having orphaned entries
        # that will never be deleted because they no longer exist in the Kubernetes API.
        self.metadata_cache_manager.clear_metadata_cache()

        while not self.stop_monitoring:
            resource_id = self.fetch_list_all_pod_for_all_namespaces()
            self.watch_list_pod_for_all_namespaces(resource_id)

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

    def fetch_list_all_pod_for_all_namespaces(self) -> int | None:
        """
        Fetch all pod for all namespaces and populate the metadata cache.
        :return: Resource version of the last fetched entry
        """
        resource_version = None
        try:
            pods: V1PodList = self.k8s_api.list_pod_for_all_namespaces(watch=False)
            resource_version = pods.metadata.resource_version
            for pod in pods.items:
                for entry in self.build_metadata_cache_entries_from_pod(pod):
                    self.metadata_cache_manager.update_container_metadata(ADDED_EVENT, entry)

        except ApiException as e:
            logging.warning('API exception caught in fetch: %s %s', e.status, e.reason)
        except ProtocolError as e:
            logging.warning('Protocol error caught in fetch: %s', e)

        return resource_version

    def watch_list_pod_for_all_namespaces(self, resource_version: int = None):
        """
        Watch k8s pods events for all namespaces and update the local metadata cache accordingly.
        :param resource_version: Resource version from where the watcher begin
        """
        try:
            w = watch.Watch()
            for event in w.stream(self.k8s_api.list_pod_for_all_namespaces, resource_version=resource_version):
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
