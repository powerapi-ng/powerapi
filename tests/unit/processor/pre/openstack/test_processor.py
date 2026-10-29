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

import pickle
from datetime import datetime
from unittest.mock import Mock, call, patch

import pytest

pytest.importorskip('openstack')

from powerapi.processor.pre.openstack.metadata_registry import OpenStackMetadataRegistry
from powerapi.processor.pre.openstack.monitor_agent import OpenStackMonitorConfig
from powerapi.processor.pre.openstack.processor import HWPCReportProcessor, OpenStackProcessor
from powerapi.report import HWPCReport


@pytest.fixture
def metadata_registry_mock() -> Mock:
    """
    Return a mocked OpenStack metadata registry.
    """
    return Mock(spec=OpenStackMetadataRegistry)


@pytest.fixture
def hwpc_report_processor(metadata_registry_mock) -> HWPCReportProcessor:
    """
    Return a processor with a mocked metadata registry.
    """
    return HWPCReportProcessor(metadata_registry_mock)


@pytest.fixture
def manager_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """
    Return a mocked multiprocessing manager.
    """
    manager = Mock(name='manager')
    monkeypatch.setattr('powerapi.processor.pre.openstack.processor.Manager', Mock(return_value=manager))
    return manager


@pytest.fixture
def registry_factory_mock(monkeypatch: pytest.MonkeyPatch, metadata_registry_mock: Mock) -> Mock:
    """
    Return a mocked OpenStack metadata registry constructor.
    """
    factory = Mock(return_value=metadata_registry_mock)
    monkeypatch.setattr('powerapi.processor.pre.openstack.processor.OpenStackMetadataRegistry', factory)
    return factory


@pytest.fixture
def monitor_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """
    Return a mocked OpenStack monitor.
    """
    monitor = Mock(name='monitor', pid=None)
    monkeypatch.setattr(
        'powerapi.processor.pre.openstack.processor.OpenStackMonitorAgent',
        Mock(return_value=monitor),
    )
    return monitor


@pytest.fixture
def openstack_processor(manager_mock, registry_factory_mock, monitor_mock) -> OpenStackProcessor:
    """
    Return an OpenStack processor with mocked lifecycle resources.
    """
    return OpenStackProcessor(Mock())


def make_libvirt_hwpc_report() -> HWPCReport:
    """
    Generate an HWPCReport for an OpenStack libvirt target.
    """
    target = '/machine.slice/machine-qemu-3-instance-00000003.scope/libvirt/emulator'
    return HWPCReport(datetime.now(), 'compute-1', target, {}, {'scope': 'pytest'})


def test_processor_adds_openstack_metadata(hwpc_report_processor, metadata_registry_mock):
    """
    Matching OpenStack reports should receive cached metadata in place.
    """
    report = make_libvirt_hwpc_report()
    original_target = report.target

    report.metadata['app'] = 'old-app'

    server_metadata = {'openstack_server_name': 'server-name', 'app': 'powerapi'}
    metadata_registry_mock.get_metadata.return_value = server_metadata

    result = hwpc_report_processor.process(report)

    assert result is report
    assert isinstance(result, HWPCReport)
    assert result.target == original_target
    assert result.metadata == {
        'scope': 'pytest',
        'openstack_server_name': 'server-name',
        'app': 'powerapi',
    }
    metadata_registry_mock.get_metadata.assert_called_once_with('compute-1', 'instance-00000003')


def test_processor_drops_report_when_server_metadata_missing(hwpc_report_processor, metadata_registry_mock):
    """
    Matching OpenStack reports should be dropped on a cache miss.
    """
    report = make_libvirt_hwpc_report()

    metadata_registry_mock.get_metadata.return_value = None

    result = hwpc_report_processor.process(report)

    assert result is None


def test_processor_preserves_non_openstack_targets(hwpc_report_processor, metadata_registry_mock):
    """
    Non-OpenStack targets should pass through without a registry lookup.
    """
    report = HWPCReport(datetime.now(), 'compute-1', 'plain-container', {}, {'scope': 'pytest'})

    result = hwpc_report_processor.process(report)

    assert result is report
    assert isinstance(result, HWPCReport)
    assert result.target == 'plain-container'
    assert result.metadata == {'scope': 'pytest'}
    metadata_registry_mock.get_metadata.assert_not_called()


def test_processor_construction_does_not_start_resources():
    """
    Processor construction should defer resource creation until initialization.
    """
    with (
        patch('powerapi.processor.pre.openstack.processor.Manager') as manager,
        patch('powerapi.processor.pre.openstack.processor.OpenStackMonitorAgent') as monitor,
    ):
        OpenStackProcessor(Mock())

    manager.assert_not_called()
    monitor.assert_not_called()


def test_processor_can_be_pickled_before_initialization():
    """
    An uninitialized processor should contain only picklable attributes.
    """
    config = OpenStackMonitorConfig(polling_interval=1.0, metadata_mapping={'pytest': 'powerapi'})
    processor = OpenStackProcessor(config)

    pickle.dumps(processor)


def test_teardown_before_initialization_is_safe(openstack_processor, manager_mock, monitor_mock):
    """
    Teardown before initialization should not attempt resource cleanup.
    """
    openstack_processor.teardown()

    monitor_mock.terminate.assert_not_called()
    monitor_mock.join.assert_not_called()
    manager_mock.shutdown.assert_not_called()


def test_get_report_processors(openstack_processor, metadata_registry_mock):
    """
    Return an HWPC report processor using the shared metadata registry.
    """
    openstack_processor.initialize()

    report_processor, = openstack_processor.get_report_processors()

    assert isinstance(report_processor, HWPCReportProcessor)
    assert report_processor.report_type is HWPCReport
    assert report_processor.metadata_registry is metadata_registry_mock


def test_processor_lifecycle(openstack_processor, manager_mock, monitor_mock):
    """
    Start monitoring and release resources in dependency order.
    """
    cleanup = Mock()
    cleanup.attach_mock(monitor_mock, 'monitor')
    cleanup.attach_mock(manager_mock, 'manager')

    openstack_processor.initialize()
    monitor_mock.start.assert_called_once_with()
    monitor_mock.pid = 123
    cleanup.reset_mock()

    openstack_processor.teardown()
    openstack_processor.teardown()

    assert cleanup.mock_calls == [
        call.monitor.terminate(),
        call.monitor.join(),
        call.manager.shutdown(),
    ]
    assert openstack_processor.manager is None
    assert openstack_processor.monitor_agent is None


def test_registry_initialization_failure_shuts_down_manager(openstack_processor, manager_mock, registry_factory_mock, monitor_mock):
    """
    Registry creation failure should release the already started manager.
    """
    registry_factory_mock.side_effect = RuntimeError('registry failed')

    with pytest.raises(RuntimeError, match='registry failed'):
        openstack_processor.initialize()

    manager_mock.shutdown.assert_called_once_with()
    monitor_mock.start.assert_not_called()
    assert openstack_processor.manager is None


def test_monitor_start_failure_shuts_down_manager(openstack_processor, manager_mock, monitor_mock):
    """
    Monitor startup failure should release the manager without joining an unstarted process.
    """
    monitor_mock.start.side_effect = RuntimeError('monitor failed')

    with pytest.raises(RuntimeError, match='monitor failed'):
        openstack_processor.initialize()

    manager_mock.shutdown.assert_called_once_with()
    monitor_mock.terminate.assert_not_called()
    monitor_mock.join.assert_not_called()
    assert openstack_processor.manager is None
    assert openstack_processor.monitor_agent is None


def test_monitor_cleanup_failure_still_shuts_down_manager(openstack_processor, manager_mock, monitor_mock):
    """
    Monitor cleanup failure should not prevent manager shutdown.
    """
    openstack_processor.initialize()
    monitor_mock.pid = 123
    monitor_mock.terminate.side_effect = RuntimeError('cleanup failed')

    with pytest.raises(RuntimeError, match='cleanup failed'):
        openstack_processor.teardown()

    manager_mock.shutdown.assert_called_once_with()
    assert openstack_processor.manager is None


def test_second_initialization_preserves_existing_resources(openstack_processor, manager_mock, monitor_mock):
    """
    Reinitializing an active processor should fail without replacing its resources.
    """
    openstack_processor.initialize()

    with pytest.raises(RuntimeError, match='already initialized'):
        openstack_processor.initialize()

    assert openstack_processor.manager is manager_mock
    assert openstack_processor.monitor_agent is monitor_mock
    monitor_mock.start.assert_called_once_with()
    manager_mock.shutdown.assert_not_called()
