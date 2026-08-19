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

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from powerapi.processor.pre.k8s.handlers import (
    ActorPoisonPillMessageHandler,
    ActorStartMessageHandler,
    HWPCReportHandler,
)
from powerapi.report import HWPCReport


@pytest.fixture
def start_message_handler():
    """
    Factory fixture creating a start message handler.
    """

    def _create_handler() -> ActorStartMessageHandler:
        actor = Mock(name='processor-actor')
        actor.target_actors = [Mock(name='target_actor_a'), Mock(name='target_actor_b')]

        state = Mock(name='state')
        state.actor = actor
        state.monitor_agent = Mock(name='monitor_agent')

        return ActorStartMessageHandler(state)

    return _create_handler


@pytest.fixture
def poison_pill_message_handler():
    """
    Factory fixture creating a Poison-Pill message handler.
    """

    def _create_handler() -> ActorPoisonPillMessageHandler:
        actor = Mock(name='processor-actor')
        actor.target_actors = [Mock(name='target_actor_a'), Mock(name='target_actor_b')]

        state = Mock(name='state')
        state.actor = actor
        state.manager = Mock(name='manager')
        state.monitor_agent = Mock(name='monitor_agent')

        return ActorPoisonPillMessageHandler(state)

    return _create_handler


@pytest.fixture
def hwpc_report_handler():
    """
    Factory fixture creating an HwPC report handler.
    """

    def _create_handler() -> tuple[HWPCReportHandler, list[HWPCReport]]:
        state = Mock(name='state')
        state.metadata_registry = Mock(name='metadata_registry')
        handler = HWPCReportHandler(state)

        reports_sent = []
        handler._send_report = Mock(side_effect=lambda msg: reports_sent.append(msg))

        return handler, reports_sent

    return _create_handler


def make_pod_hwpc_report() -> tuple[HWPCReport, str]:
    """
    Generate an HWPCReport for a Kubernetes pod target.
    :returns: HWPCReport object and the container ID of the target
    """
    timestamp = datetime.now()
    sensor = 'pytest'
    metadata = {'scope': 'pytest'}
    container_id = '4302a9acd86a9d21b745bf695a453915f5416151cb2b0dd9fef74f3860f5c286'
    target = Path(
        '/kubepods.slice'
        '/kubepods-burstable.slice'
        '/kubepods-burstable-poda355c9c2_78a3_40ce_9326_037ba57681e8.slice'
        f'/cri-containerd-{container_id}.scope'
    )

    return HWPCReport(timestamp, sensor, str(target), {}, metadata), container_id


def test_start_handler_connects_targets_and_starts_monitor(start_message_handler):
    """
    The start handler should connect target actors and start monitoring.
    """
    handler = start_message_handler()

    handler.initialization()

    handler.state.monitor_agent.start.assert_called_once()
    for actor in handler.state.actor.target_actors:
        actor.connect_data.assert_called_once()


def test_poison_pill_handler_stops_resources_and_disconnects_targets(poison_pill_message_handler):
    """
    The Poison-Pill handler should stop resources and disconnect targets.
    """
    handler = poison_pill_message_handler()

    handler.teardown()

    handler.state.monitor_agent.terminate.assert_called_once()
    handler.state.monitor_agent.join.assert_called_once()
    handler.state.manager.shutdown.assert_called_once()
    for actor in handler.state.actor.target_actors:
        actor.disconnect.assert_called_once()


def test_hwpc_report_handler_adds_k8s_metadata_and_forwards_report(hwpc_report_handler):
    """
    Test that the HwPC report handler forwards a report for a valid k8s target when it is in the metadata cache.
    """
    handler, reports_sent = hwpc_report_handler()
    report, container_id = make_pod_hwpc_report()

    k8s_metadata = {
        'k8s_container_name': 'powerapi-test-container',
        'k8s_pod_namespace': 'powerapi-test-namespace',
        'k8s_pod_name': 'powerapi-test-pod',
        'k8s_label_app': 'powerapi',
    }
    handler.state.metadata_registry.get_metadata.return_value = k8s_metadata

    handler.handle(report)

    handler.state.metadata_registry.get_metadata.assert_called_once_with(container_id)
    assert reports_sent == [report]
    (processed_report,) = reports_sent

    assert processed_report.target == report.target
    assert processed_report.metadata == report.metadata | k8s_metadata


def test_hwpc_report_handler_drops_report_when_container_metadata_missing(hwpc_report_handler):
    """
    Test that the HwPC report handler don't forward a report for a valid k8s target when it is not in the metadata cache.
    """
    handler, reports_sent = hwpc_report_handler()
    report, _ = make_pod_hwpc_report()

    handler.state.metadata_registry.get_metadata.return_value = None

    handler.handle(report)

    handler.state.metadata_registry.get_metadata.assert_called_once()
    assert reports_sent == []


def test_hwpc_report_handler_forwards_non_k8s_targets(hwpc_report_handler):
    """
    Test that the HwPC report handler forwards a report that is not a k8s target.
    """
    handler, reports_sent = hwpc_report_handler()
    report = HWPCReport(datetime.now(), 'pytest', 'test-container', {}, {'scope': 'pytest'})

    handler.handle(report)

    assert reports_sent == [report]
    (processed_report,) = reports_sent

    assert processed_report.target == 'test-container'
    assert processed_report.metadata == {'scope': 'pytest'}
    handler.state.metadata_registry.get_metadata.assert_not_called()
