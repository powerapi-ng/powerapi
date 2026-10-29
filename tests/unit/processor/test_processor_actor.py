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

from powerapi.actor import PoisonPillMessageHandler, StartMessageHandler
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.processor import Processor, ProcessorActor, ReportProcessor
from powerapi.processor.handlers import ProcessorReportHandler
from powerapi.processor.processor_actor import ProcessorState
from powerapi.report import HWPCReport, PowerReport


@pytest.fixture
def report():
    """
    Return an HWPC report for processor tests.
    """
    return HWPCReport(datetime.now(), 'pytest', 'pytest', {})


@pytest.fixture
def report_processor(report):
    """
    Return a mocked HWPC report processor.
    """
    processor = Mock(spec=ReportProcessor)
    processor.report_type = HWPCReport
    processor.process.return_value = report
    return processor


@pytest.fixture
def processor_state(report_processor):
    """
    Return a processor state with mocked resources and target actors.
    """
    actor = Mock(name='processor-actor')
    actor.target_actors = [Mock(), Mock()]
    processor = Mock(spec=Processor)
    processor.get_report_processors.return_value = (report_processor,)
    state = ProcessorState(actor, processor)
    actor.add_handler.side_effect = state.add_handler
    return state


@pytest.fixture
def report_handler(processor_state, report_processor):
    """
    Return a report handler using the mocked processor state.
    """
    return ProcessorReportHandler(processor_state, report_processor)


@pytest.mark.parametrize(
    ('message', 'handler_type'),
    [
        (StartMessage(), StartMessageHandler),
        (PoisonPillMessage(), PoisonPillMessageHandler),
    ],
)
def test_actor_registers_lifecycle_handlers(message, handler_type):
    """
    Actor setup should register lifecycle handlers using its processor state.
    """
    actor = ProcessorActor('pytest', Mock(spec=Processor))

    actor.setup()

    handler = actor.state.get_corresponding_handler(message)
    assert isinstance(handler, handler_type)
    assert handler.state is actor.state


def test_actor_setup_does_not_initialize_processor():
    """
    Actor construction and setup should defer processor initialization.
    """
    processor = Mock(spec=Processor)

    actor = ProcessorActor('pytest', processor)
    actor.setup()

    processor.initialize.assert_not_called()
    processor.get_report_processors.assert_not_called()


def test_state_initialization_connects_targets_and_initializes_processor(processor_state):
    """
    State initialization should connect targets and initialize the component once.
    """
    processor_state.initialize()

    for target in processor_state.actor.target_actors:
        target.connect_data.assert_called_once_with()

    processor_state.processor.initialize.assert_called_once_with()
    processor_state.processor.get_report_processors.assert_called_once_with()


def test_state_initialization_registers_all_report_processors(processor_state, report_processor):
    """
    State initialization should register every implementation for its report type.
    """
    power_processor = Mock(spec=ReportProcessor)
    power_processor.report_type = PowerReport
    processor_state.processor.get_report_processors.return_value = (report_processor, power_processor)

    processor_state.initialize()

    registered_types = [call.args[0] for call in processor_state.actor.add_handler.call_args_list]
    assert registered_types == [HWPCReport, PowerReport]


@pytest.mark.parametrize('method', ['initialize', 'get_report_processors'])
def test_failed_initialization_does_not_acknowledge_success(processor_state, method):
    """
    Component startup failures should propagate without acknowledging initialization.
    """
    getattr(processor_state.processor, method).side_effect = RuntimeError('startup failed')
    handler = StartMessageHandler(processor_state)

    with pytest.raises(RuntimeError, match='startup failed'):
        handler.handle(StartMessage())

    assert not processor_state.initialized
    processor_state.actor.send_control.assert_not_called()


def test_state_teardown_releases_processor_and_disconnects_targets(processor_state):
    """
    State teardown should release the component and disconnect every target.
    """
    processor_state.teardown()

    processor_state.processor.teardown.assert_called_once_with()
    for target in processor_state.actor.target_actors:
        target.disconnect.assert_called_once_with()


def test_state_teardown_disconnects_targets_when_processor_cleanup_fails(processor_state):
    """
    Component cleanup failures should not leave target connections open.
    """
    processor_state.processor.teardown.side_effect = RuntimeError('cleanup failed')

    with pytest.raises(RuntimeError, match='cleanup failed'):
        processor_state.teardown()

    for target in processor_state.actor.target_actors:
        target.disconnect.assert_called_once_with()


def test_report_handler_forwards_processed_report(report_handler, report_processor, report):
    """
    Every target should receive the report returned by the processing implementation.
    """
    processed_report = HWPCReport(report.timestamp, report.sensor, report.target, {}, {'scope': 'processed'})
    report_processor.process.return_value = processed_report

    report_handler.handle(report)

    report_processor.process.assert_called_once_with(report)
    for target in report_handler.state.actor.target_actors:
        target.send_data.assert_called_once_with(processed_report)


def test_report_handler_drops_report_and_processes_next_one(report_handler, report_processor, report):
    """
    A dropped report should not be forwarded or prevent processing the next report.
    """
    report_processor.process.side_effect = [None, report]

    report_handler.handle(report)
    for target in report_handler.state.actor.target_actors:
        target.send_data.assert_not_called()

    report_handler.handle(report)

    for target in report_handler.state.actor.target_actors:
        target.send_data.assert_called_once_with(report)


def test_report_types_use_their_own_processing_implementations(processor_state, report_processor, report):
    """
    Different report types should share a lifecycle and reach their own processors.
    """
    power_report = PowerReport(report.timestamp, report.sensor, report.target, 1.0)
    power_processor = Mock(spec=ReportProcessor)
    power_processor.report_type = PowerReport
    power_processor.process.return_value = power_report
    component = processor_state.processor
    component.get_report_processors.return_value = (report_processor, power_processor)
    StartMessageHandler(processor_state).handle(StartMessage())

    processor_state.handle_message(report)
    processor_state.handle_message(power_report)
    processor_state.teardown()

    component.initialize.assert_called_once_with()
    component.get_report_processors.assert_called_once_with()
    component.teardown.assert_called_once_with()
    report_processor.process.assert_called_once_with(report)
    power_processor.process.assert_called_once_with(power_report)
    for target in processor_state.actor.target_actors:
        assert [call.args[0] for call in target.send_data.call_args_list] == [report, power_report]
