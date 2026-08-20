# Copyright (c) 2026, Inria
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
from datetime import datetime
from unittest.mock import Mock, call

import pytest

pytest.importorskip('openstack')

from openstack.exceptions import SDKException

from powerapi.processor.pre.openstack.metadata_registry import OpenStackMetadataRegistry
from powerapi.processor.pre.openstack.monitor_agent import (
    OpenStackMonitorAgent,
    OpenStackMonitorConfig,
)


@pytest.fixture
def monitor_agent():
    """
    Return an OpenStack monitor agent using mocked collaborators.
    """
    registry = Mock(spec=OpenStackMetadataRegistry)
    config = OpenStackMonitorConfig(polling_interval=1.0, metadata_mapping={})
    agent = OpenStackMonitorAgent(registry, config)
    agent.server_change_handler = Mock()
    return agent


@pytest.fixture
def configure_monitor_agent(monitor_agent):
    """
    Configure the monitor agent for a finite run without external calls.
    """

    def _configure(
        *,
        fetch_server_changes: Mock | None = None,
        stop_event: Mock | None = None,
        wait_results: Iterable[bool] = (True,),
    ) -> OpenStackMonitorAgent:
        if fetch_server_changes is None:
            fetch_server_changes = Mock(return_value='pytest')
        if stop_event is None:
            stop_event = Mock(spec_set=['is_set', 'wait'])

        stop_event.is_set.return_value = False
        stop_event.wait.side_effect = wait_results

        monitor_agent._setup_signal_handlers = Mock()
        monitor_agent._setup_openstack_api_client = Mock()
        monitor_agent._stop_monitoring = stop_event
        monitor_agent.fetch_server_changes = fetch_server_changes
        return monitor_agent

    return _configure


def test_initial_fetch_forwards_all_servers(monitor_agent):
    """
    The initial synchronization should fetch and handle every server.
    """
    servers = [Mock(name='first_server'), Mock(name='second_server')]
    openstack_api = Mock()
    openstack_api.compute.servers.return_value = servers

    next_changes_since = monitor_agent.fetch_server_changes(openstack_api)

    openstack_api.compute.servers.assert_called_once_with(details=True, all_projects=True)
    assert monitor_agent.server_change_handler.handle.call_args_list == [call(servers[0]), call(servers[1])]
    assert datetime.fromisoformat(next_changes_since).tzinfo is not None


def test_incremental_fetch_uses_previous_synchronization_timestamp(monitor_agent):
    """
    Later synchronizations should request only servers changed since the previous one.
    """
    openstack_api = Mock()
    openstack_api.compute.servers.return_value = []

    monitor_agent.fetch_server_changes(openstack_api, '2026-08-19T12:00:00+00:00')

    openstack_api.compute.servers.assert_called_once_with(
        details=True,
        all_projects=True,
        changes_since='2026-08-19T12:00:00+00:00',
    )


@pytest.mark.parametrize(
    'exception',
    [
        pytest.param(SDKException('pytest'), id='sdk-error'),
        pytest.param(AttributeError('pytest'), id='missing-attribute'),
        pytest.param(ValueError('pytest'), id='invalid-attribute'),
    ],
)
def test_run_waits_after_fetch_failure(configure_monitor_agent, exception):
    """
    A failed synchronization should wait before leaving or retrying the loop.
    """
    fetch_server_changes = Mock(side_effect=exception)
    stop_event = Mock()
    monitor_agent = configure_monitor_agent(
        fetch_server_changes=fetch_server_changes,
        stop_event=stop_event,
    )

    monitor_agent.run()

    fetch_server_changes.assert_called_once()
    stop_event.wait.assert_called_once()


def test_run_uses_successful_synchronization_timestamp(configure_monitor_agent):
    """
    A successful synchronization should provide its timestamp to the next one.
    """
    fetch_server_changes = Mock(side_effect=['first-sync', 'second-sync'])
    monitor_agent = configure_monitor_agent(
        fetch_server_changes=fetch_server_changes,
        wait_results=[False, True],
    )

    monitor_agent.run()

    assert [change.args[1] for change in fetch_server_changes.call_args_list] == [None, 'first-sync']


def test_run_preserves_synchronization_timestamp_after_failure(configure_monitor_agent):
    """
    A failed synchronization should retry from the last successful timestamp.
    """
    fetch_server_changes = Mock(side_effect=['first-sync', SDKException('pytest'), 'second-sync'])
    monitor_agent = configure_monitor_agent(
        fetch_server_changes=fetch_server_changes,
        wait_results=[False, False, True],
    )

    monitor_agent.run()

    assert [change.args[1] for change in fetch_server_changes.call_args_list] == [
        None,
        'first-sync',
        'first-sync',
    ]
