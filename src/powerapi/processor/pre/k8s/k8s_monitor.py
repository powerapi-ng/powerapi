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

from logging import Formatter, getLogger, Logger, StreamHandler, WARNING
from multiprocessing import Manager, Process

from kubernetes import client, config, watch
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException

from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorState, K8sMetadataCacheManager, \
    K8sPodUpdateMetadata, DELETED_EVENT, ADDED_EVENT, MODIFIED_EVENT

LOCAL_CONFIG_MODE = "local"
MANUAL_CONFIG_MODE = "manual"
CLUSTER_CONFIG_MODE = "cluster"

MANUAL_CONFIG_API_KEY_DEFAULT_VALUE = "YOUR_API_KEY"
MANUAL_CONFIG_HOST_DEFAULT_VALUE = "http://localhost"

v1_api = None

manual_config_api_key = MANUAL_CONFIG_API_KEY_DEFAULT_VALUE
manual_config_host = MANUAL_CONFIG_HOST_DEFAULT_VALUE


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
    configuration.api_key["authorization"] = manual_config_api_key
    # Defining host is optional and default to http://localhost
    configuration.host = manual_config_host
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


def get_core_v1_api(logger: Logger, mode: str = None, api_key: str = None, host: str = None):
    """
    Returns a handler to the k8s API.
    """
    global v1_api
    global manual_config_api_key
    global manual_config_host
    if v1_api is None:
        if api_key:
            manual_config_api_key = api_key
        if host:
            manual_config_host = host
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

        # Concerned Actor state
        self.concerned_actor_state = concerned_actor_state

        # Multiprocessing Manager
        self.manager = Manager()

        # Shared cache
        self.concerned_actor_state.metadata_cache_manager = K8sMetadataCacheManager(process_manager=self.manager,
                                                                                    level_logger=level_logger)

        self.stop_monitoring = self.manager.Event()

        self.stop_monitoring.clear()

    def run(self):
        """
        Main code executed by the Monitor
        """
        self.query_k8s()

    def query_k8s(self):
        """
        Query k8s for changes and update the metadata cache
        """
        try:
            while not self.stop_monitoring.is_set():
                events = self.k8s_streaming_query()
                for event in events:
                    event_type, namespace, pod_name, container_ids, labels = event

                    self.concerned_actor_state.metadata_cache_manager.update_cache(metadata=K8sPodUpdateMetadata(
                        event=event_type,
                        namespace=namespace,
                        pod=pod_name,
                        containers_id=container_ids,
                        labels=labels
                    )
                    )

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
        Return a list of events by using the provided parameters
        :param int timeout_seconds: Timeout in seconds for waiting for events
        :param str k8sapi_mode: Kind of API mode
        """
        api = get_core_v1_api(mode=self.concerned_actor_state.k8s_api_mode, logger=self.logger,
                              api_key=self.concerned_actor_state.api_key, host=self.concerned_actor_state.host)
        events = []
        w = watch.Watch()

        try:
            event = None
            for event in w.stream(
                    func=api.list_pod_for_all_namespaces, timeout_seconds=self.concerned_actor_state.timeout_query
            ):

                if event:

                    if event["type"] not in {DELETED_EVENT, ADDED_EVENT, MODIFIED_EVENT}:
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
