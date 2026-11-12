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
from collections.abc import Mapping
from dataclasses import dataclass
from multiprocessing import Event, Process
from signal import SIGINT, SIGTERM, signal

from kubernetes.client import ApiClient, ApiException, Configuration, CoreV1Api
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.watch import Watch
from urllib3.exceptions import ProtocolError

from .metadata_registry import KubernetesMetadataRegistry
from .pod_event_handler import KubernetesPodEventHandler

K8S_MONITOR_RETRY_DELAY_SECONDS = 5.0


@dataclass(frozen=True)
class KubernetesMonitorConfig:
    """
    Kubernetes monitoring agent configuration.
    :param api_mode: Kubernetes API mode (manual, local, cluster)
    :param api_host: Kubernetes API host to connect to
    :param api_key: Kubernetes API key (Bearer Token) to authenticate with
    :param label_mapping: Mapping from Kubernetes pod label names to canonical report metadata names
    """
    api_mode: str
    api_host: str | None
    api_key: str | None
    label_mapping: Mapping[str, str]


def load_manual_k8s_config(configuration: Configuration, api_host: str | None, api_key: str | None) -> None:
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


def build_k8s_api_client_configuration(api_mode: str, api_host: str | None, api_key: str | None) -> Configuration:
    """
    Build a Kubernetes API client configuration.
    :param api_mode: The Kubernetes API mode (manual, local, cluster)
    :param api_host: The Kubernetes API host
    :param api_key: The Kubernetes API key (Bearer Token)
    :return: Kubernetes API client configuration
    """
    configuration = Configuration()
    match api_mode.casefold():
        case 'local':
            # Setup Kubernetes API client with a kube-config file. (from KUBECONFIG environment variable, or ~/.kube/config)
            load_kube_config(client_configuration=configuration)
        case 'cluster':
            # Setup Kubernetes API client with the pod service account. (requires PowerAPI to be running in a pod)
            load_incluster_config(client_configuration=configuration)
        case 'manual':
            load_manual_k8s_config(configuration, api_host, api_key)
        case _:
            raise ValueError(f'Invalid Kubernetes API mode: {api_mode}')

    return configuration


class KubernetesMonitorAgent(Process):
    """
    Background monitoring agent that update the shared metadata cache from Kubernetes API events.
    """

    def __init__(self, registry: KubernetesMetadataRegistry, config: KubernetesMonitorConfig, level_logger: int = logging.WARNING):
        """
        :param registry: Metadata cache registry
        :param config: Configuration of the monitoring agent
        :param level_logger: The logger level
        """
        super().__init__(name='k8s-processor-monitor-agent')

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level_logger)
        formatter = logging.Formatter('%(asctime)s || %(levelname)s || ' + '%(process)d %(processName)s || %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.config = config
        self.pod_event_handler = KubernetesPodEventHandler(registry, config.label_mapping)

        self._stop_monitoring = Event()

    @staticmethod
    def build_k8s_api_client(api_config: Configuration) -> CoreV1Api:
        """
        Build a Kubernetes API client with the given configuration.
        :param api_config: Kubernetes API configuration
        :return: Kubernetes API client
        """
        api_client = ApiClient(configuration=api_config)
        return CoreV1Api(api_client)

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for the current Process.
        """
        def stop_monitor(_, __):
            self._stop_monitoring.set()
            sys.exit(0)

        signal(SIGTERM, stop_monitor)
        signal(SIGINT, stop_monitor)

    def run(self) -> None:
        """
        Main code executed by the Kubernetes monitor agent.
        """
        self._setup_signal_handlers()

        api_config = build_k8s_api_client_configuration(self.config.api_mode, self.config.api_host, self.config.api_key)
        api_client = self.build_k8s_api_client(api_config)

        while not self._stop_monitoring.is_set():
            try:
                resource_id = self.fetch_list_all_pod_for_all_namespaces(api_client)
                self.watch_list_pod_for_all_namespaces(api_client, resource_id)
            except ApiException as e:
                logging.error("Kubernetes API request failed: %s %s", e.status, e.reason)
            except ProtocolError as e:
                logging.error("Failed to connect to Kubernetes API: %s", e)

            if self._stop_monitoring.wait(K8S_MONITOR_RETRY_DELAY_SECONDS):
                break

    def fetch_list_all_pod_for_all_namespaces(self, api_client: CoreV1Api) -> str | None:
        """
        Fetch all pod for all namespaces and populate the metadata cache.
        :param api_client: Kubernetes api client
        :return: Resource version of the last fetched entry
        """
        pods = api_client.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            self.pod_event_handler.handle("ADDED", pod)

        return pods.metadata.resource_version

    def watch_list_pod_for_all_namespaces(self, api_client: CoreV1Api, resource_version: str | None = None) -> None:
        """
        Watch k8s pods events for all namespaces and update the local metadata cache accordingly.
        :param api_client: Kubernetes API client
        :param resource_version: Resource version from where the watcher begin
        """
        w = Watch()
        try:
            for event in w.stream(api_client.list_pod_for_all_namespaces, resource_version=resource_version):
                self.pod_event_handler.handle(event["type"], event["object"])
        except ValueError as e:
            logging.warning("Failed to process event: %s", e)
        finally:
            w.stop()
