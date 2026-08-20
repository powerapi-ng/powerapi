# Copyright (c) 2023, Inria
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

from collections.abc import Iterable
from unittest.mock import Mock, call, patch, sentinel

import pytest

pytest.importorskip('kubernetes')

from kubernetes.client import ApiException, CoreV1Api
from urllib3.exceptions import ProtocolError

from powerapi.processor.pre.k8s.metadata_registry import KubernetesMetadataRegistry
from powerapi.processor.pre.k8s.monitor_agent import (
    KubernetesMonitorAgent,
    KubernetesMonitorConfig,
    build_k8s_api_client_configuration,
)
from powerapi.processor.pre.k8s.pod_event_handler import KubernetesPodEventHandler


@pytest.fixture
def pod_event_handler():
    """
    Return a mocked Pod event handler.
    """
    return Mock(spec=KubernetesPodEventHandler)


@pytest.fixture
def monitor_agent(pod_event_handler):
    """
    Return a monitor agent with a mocked Pod event handler.
    """
    config = KubernetesMonitorConfig(
        api_mode='manual',
        api_host='https://localhost:6443',
        api_key='pytest-token',
        label_mapping={},
    )
    agent = KubernetesMonitorAgent(Mock(spec=KubernetesMetadataRegistry), config)
    agent.pod_event_handler = pod_event_handler
    return agent


@pytest.fixture
def watcher():
    """
    Return the watcher created by the monitor agent.
    """
    with patch('powerapi.processor.pre.k8s.monitor_agent.Watch', autospec=True) as watch_class:
        yield watch_class.return_value


@pytest.fixture
def configure_monitor_agent(monitor_agent):
    """
    Configure the monitor agent for a finite run without external calls.
    """

    def _configure(
        *,
        fetch_pods: Mock | None = None,
        watch_pods: Mock | None = None,
        stop_event: Mock | None = None,
        wait_results: Iterable[bool] = (True,),
    ) -> KubernetesMonitorAgent:
        if fetch_pods is None:
            fetch_pods = Mock(return_value='pytest')
        if watch_pods is None:
            watch_pods = Mock()
        if stop_event is None:
            stop_event = Mock(spec_set=['is_set', 'wait'])

        stop_event.is_set.return_value = False
        stop_event.wait.side_effect = wait_results

        monitor_agent._setup_signal_handlers = Mock()
        monitor_agent._stop_monitoring = stop_event
        monitor_agent.fetch_list_all_pod_for_all_namespaces = fetch_pods
        monitor_agent.watch_list_pod_for_all_namespaces = watch_pods
        return monitor_agent

    return _configure


def test_build_manual_configuration_sets_bearer_authentication():
    """
    Manual configuration should set the API endpoint and bearer token.
    """
    configuration = build_k8s_api_client_configuration(
        'manual',
        'https://powerapi:6443',
        'pytest-token',
    )

    assert configuration.host == 'https://powerapi:6443'
    assert configuration.api_key['authorization'] == 'pytest-token'
    assert configuration.api_key_prefix['authorization'] == 'Bearer'


def test_build_manual_configuration_requires_api_host():
    """
    Manual configuration should reject a missing API host.
    """
    with pytest.raises(ValueError, match='Kubernetes API host is not defined'):
        build_k8s_api_client_configuration('manual', None, 'pytest-token')


def test_build_manual_configuration_requires_api_key():
    """
    Manual configuration should reject a missing API key.
    """
    with pytest.raises(ValueError, match='Kubernetes API key is not defined'):
        build_k8s_api_client_configuration('manual', 'https://localhost:6443', None)


def test_build_configuration_rejects_unknown_mode():
    """
    An unsupported Kubernetes API mode should be rejected.
    """
    with pytest.raises(ValueError, match='Invalid Kubernetes API mode'):
        build_k8s_api_client_configuration('pytest', None, None)


def test_fetch_forwards_pods_and_returns_resource_version(monitor_agent, pod_event_handler):
    """
    The initial list should be forwarded as added events.
    """
    api_client = Mock(spec=CoreV1Api)
    api_client.list_pod_for_all_namespaces.return_value = Mock(
        metadata=Mock(resource_version='42'),
        items=[sentinel.first_pod, sentinel.second_pod],
    )

    resource_version = monitor_agent.fetch_list_all_pod_for_all_namespaces(api_client)

    assert resource_version == '42'
    api_client.list_pod_for_all_namespaces.assert_called_once_with(watch=False)
    assert pod_event_handler.handle.call_args_list == [
        call('ADDED', sentinel.first_pod),
        call('ADDED', sentinel.second_pod),
    ]


def test_watch_forwards_events(monitor_agent, pod_event_handler, watcher):
    """
    Watch events should be delegated in stream order.
    """
    api_client = Mock(spec=CoreV1Api)
    watcher.stream.return_value = iter([
        {'type': 'ADDED', 'object': sentinel.added_pod},
        {'type': 'MODIFIED', 'object': sentinel.modified_pod},
    ])

    monitor_agent.watch_list_pod_for_all_namespaces(api_client, '42')

    watcher.stream.assert_called_once()
    assert watcher.stream.call_args.kwargs['resource_version'] == '42'
    assert pod_event_handler.handle.call_args_list == [
        call('ADDED', sentinel.added_pod),
        call('MODIFIED', sentinel.modified_pod),
    ]
    watcher.stop.assert_called_once()


def test_watch_stops_before_propagating_transport_failure(monitor_agent, watcher):
    """
    A transport failure should propagate after watcher cleanup.
    """
    api_client = Mock(spec=CoreV1Api)
    watcher.stream.side_effect = ProtocolError('pytest')

    with pytest.raises(ProtocolError):
        monitor_agent.watch_list_pod_for_all_namespaces(api_client, '42')

    watcher.stop.assert_called_once()


def test_watch_handles_invalid_event(monitor_agent, pod_event_handler, watcher):
    """
    An invalid event should end the watch without escaping the monitor.
    """
    api_client = Mock(spec=CoreV1Api)
    watcher.stream.return_value = iter([
        {'type': 'PYTEST', 'object': sentinel.invalid_pod},
    ])
    pod_event_handler.handle.side_effect = ValueError('unexpected event')

    monitor_agent.watch_list_pod_for_all_namespaces(api_client, '42')

    pod_event_handler.handle.assert_called_once_with('PYTEST', sentinel.invalid_pod)
    watcher.stop.assert_called_once()


def test_run_waits_after_fetch_failure_without_starting_watch(configure_monitor_agent):
    """
    A failed initial list should delay the retry without starting a watch.
    """
    stop_event = Mock()
    fetch_pods = Mock(side_effect=ApiException(status=500, reason='pytest'))
    watch_pods = Mock()
    monitor_agent = configure_monitor_agent(
        fetch_pods=fetch_pods,
        watch_pods=watch_pods,
        stop_event=stop_event,
    )

    monitor_agent.run()

    fetch_pods.assert_called_once()
    watch_pods.assert_not_called()
    stop_event.wait.assert_called_once()


def test_run_waits_after_watch_failure(configure_monitor_agent):
    """
    A failed watch should delay the retry after the initial list.
    """
    stop_event = Mock()
    watch_pods = Mock(side_effect=ProtocolError('pytest'))
    monitor_agent = configure_monitor_agent(watch_pods=watch_pods, stop_event=stop_event)

    monitor_agent.run()

    watch_pods.assert_called_once()
    stop_event.wait.assert_called_once()


def test_run_retries_after_delay(configure_monitor_agent):
    """
    The monitor should start another list-watch cycle after the retry delay.
    """
    fetch_pods = Mock(side_effect=[ProtocolError('pytest'), '42'])
    watch_pods = Mock()
    monitor_agent = configure_monitor_agent(
        fetch_pods=fetch_pods,
        watch_pods=watch_pods,
        wait_results=[False, True],
    )

    monitor_agent.run()

    assert fetch_pods.call_count == 2
    watch_pods.assert_called_once()
