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
from unittest.mock import Mock

import pytest

from powerapi.processor.pre.openstack.handlers import HWPCReportHandler
from powerapi.processor.pre.openstack.metadata_cache_manager import ServerMetadata
from powerapi.report import HWPCReport


@pytest.fixture
def hwpc_report_handler():
    """
    Factory fixture creating an HwPC report handler.
    """

    def _create_handler() -> tuple[HWPCReportHandler, list[HWPCReport]]:
        actor = Mock(name='processor-actor')
        actor.target_actors = [Mock(name='target_actor_a'), Mock(name='target_actor_b')]

        state = Mock()
        state.actor = actor
        state.metadata_cache_manager = Mock(name='metadata_cache_manager')

        handler = HWPCReportHandler(state)

        reports_sent = []
        handler._send_report = Mock(side_effect=lambda msg: reports_sent.append(msg))

        return handler, reports_sent

    return _create_handler


def make_libvirt_hwpc_report() -> HWPCReport:
    """
    Generate an HWPCReport for an OpenStack libvirt target.
    """
    target = '/machine.slice/machine-qemu-3-instance-00000003.scope/libvirt/emulator'
    return HWPCReport(datetime.now(), 'compute-1', target, {}, {'scope': 'pytest'})


def test_hwpc_report_handler_adds_openstack_metadata_and_forwards_report(hwpc_report_handler):
    """
    Test that the OpenStack report handler forwards a report when metadata is in the cache.
    """
    handler, reports_sent = hwpc_report_handler()
    report = make_libvirt_hwpc_report()

    server_metadata = ServerMetadata(
        'server-id',
        'server-name',
        'compute-1',
        'instance-00000003',
        {'app': 'powerapi'}
    )
    handler.state.metadata_cache_manager.get_server_metadata.return_value = server_metadata

    handler.handle(report)

    assert reports_sent == [report]
    (processed_report,) = reports_sent

    assert processed_report.target == server_metadata.server_name
    assert processed_report.metadata['openstack'] == vars(server_metadata)
    assert processed_report.metadata['scope'] == 'pytest'
    handler.state.metadata_cache_manager.get_server_metadata.assert_called_once_with('compute-1', 'instance-00000003')


def test_hwpc_report_handler_drops_report_when_server_metadata_missing(hwpc_report_handler):
    """
    Test that the OpenStack report handler drops a report when server metadata is missing.
    """
    handler, reports_sent = hwpc_report_handler()
    report = make_libvirt_hwpc_report()

    handler.state.metadata_cache_manager.get_server_metadata.return_value = None

    handler.handle(report)

    assert reports_sent == []


def test_hwpc_report_handler_forwards_non_openstack_targets(hwpc_report_handler):
    """
    Test that the OpenStack report handler forwards non-OpenStack targets unchanged.
    """
    handler, reports_sent = hwpc_report_handler()
    report = HWPCReport(datetime.now(), 'compute-1', 'plain-container', {}, {'scope': 'pytest'})

    handler.handle(report)

    assert reports_sent == [report]
    (processed_report,) = reports_sent

    assert processed_report.target == 'plain-container'
    assert processed_report.metadata == {'scope': 'pytest'}
    handler.state.metadata_cache_manager.get_server_metadata.assert_not_called()
