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
from unittest.mock import Mock, call

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
def processor(report_processor):
    """
    Return a component providing the mocked HWPC report processor.
    """
    processor = Mock(spec=Processor)
    processor.get_report_processors.return_value = (report_processor,)
    return processor


@pytest.fixture
def processor_state(processor):
    """
    Return a processor state with mocked resources and target actors.
    """
    actor = Mock(name='processor-actor')
    actor.target_actors = [Mock(), Mock()]
    state = ProcessorState(actor, (processor,))
    actor.add_handler.side_effect = state.add_handler
    return state


@pytest.fixture
def report_handler(processor_state, report_processor):
    """
    Return a report handler using the mocked processor state.
    """
    return ProcessorReportHandler(processor_state, (report_processor,))


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
    actor = ProcessorActor('pytest', (Mock(spec=Processor),))

    actor.setup()

    handler = actor.state.get_corresponding_handler(message)
    assert isinstance(handler, handler_type)
    assert handler.state is actor.state


def test_actor_setup_does_not_initialize_processors():
    """
    Actor setup should preserve all processors without initializing them.
    """
    processors = (Mock(spec=Processor), Mock(spec=Processor))

    actor = ProcessorActor('pytest', iter(processors))
    actor.setup()

    assert actor.processors == processors
    assert actor.state.processors == processors
    for processor in processors:
        processor.initialize.assert_not_called()
        processor.get_report_processors.assert_not_called()


def test_state_initialization_connects_targets_and_initializes_processor(processor_state, processor):
    """
    State initialization should connect targets and initialize the component once.
    """
    processor_state.initialize()

    for target in processor_state.actor.target_actors:
        target.connect_data.assert_called_once_with()

    processor.initialize.assert_called_once_with()
    processor.get_report_processors.assert_called_once_with()


def test_state_initialization_registers_all_report_processors(processor_state, processor, report_processor):
    """
    State initialization should register every implementation for its report type.
    """
    power_processor = Mock(spec=ReportProcessor)
    power_processor.report_type = PowerReport
    processor.get_report_processors.return_value = (report_processor, power_processor)

    processor_state.initialize()

    registered_types = [handler_call.args[0] for handler_call in processor_state.actor.add_handler.call_args_list]
    assert registered_types == [HWPCReport, PowerReport]


def test_failed_initialization_cleans_up_started_processors(processor_state, processor):
    """
    Startup failures should release initialized components without acknowledging success.
    """
    failing_processor = Mock(spec=Processor)
    remaining_processor = Mock(spec=Processor)
    failing_processor.initialize.side_effect = RuntimeError('startup failed')
    processor_state.processors = (processor, failing_processor, remaining_processor)

    with pytest.raises(RuntimeError, match='startup failed'):
        StartMessageHandler(processor_state).handle(StartMessage())

    processor_state.teardown()

    assert not processor_state.initialized
    processor_state.actor.send_control.assert_not_called()
    processor.teardown.assert_called_once_with()
    failing_processor.teardown.assert_not_called()
    remaining_processor.initialize.assert_not_called()
    remaining_processor.teardown.assert_not_called()


def test_failed_report_processor_discovery_cleans_up_processor(processor_state, processor):
    """
    Discovery failures should release the initialized component without acknowledging success.
    """
    processor.get_report_processors.side_effect = RuntimeError('discovery failed')

    with pytest.raises(RuntimeError, match='discovery failed'):
        StartMessageHandler(processor_state).handle(StartMessage())

    processor_state.teardown()

    assert not processor_state.initialized
    processor_state.actor.send_control.assert_not_called()
    processor.teardown.assert_called_once_with()


def test_state_teardown_releases_processor_and_disconnects_targets(processor_state, processor):
    """
    State teardown should release the component and disconnect every target.
    """
    processor_state.initialize()
    processor_state.teardown()

    processor.teardown.assert_called_once_with()
    for target in processor_state.actor.target_actors:
        target.disconnect.assert_called_once_with()


def test_state_teardown_disconnects_targets_when_processor_cleanup_fails(processor_state, processor):
    """
    Component cleanup failures should not leave target connections open.
    """
    processor_state.initialize()
    processor.teardown.side_effect = RuntimeError('cleanup failed')

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


def test_report_types_use_their_own_processing_implementations(processor_state, processor, report_processor, report):
    """
    Different report types should reach their own processors and forward their results.
    """
    power_report = PowerReport(report.timestamp, report.sensor, report.target, 1.0)
    power_processor = Mock(spec=ReportProcessor)
    power_processor.report_type = PowerReport
    power_processor.process.return_value = power_report
    processor.get_report_processors.return_value = (report_processor, power_processor)
    StartMessageHandler(processor_state).handle(StartMessage())

    processor_state.handle_message(report)
    processor_state.handle_message(power_report)

    report_processor.process.assert_called_once_with(report)
    power_processor.process.assert_called_once_with(power_report)
    for target in processor_state.actor.target_actors:
        assert [send_call.args[0] for send_call in target.send_data.call_args_list] == [report, power_report]


def test_processors_share_actor_and_preserve_chain_order(processor_state, processor, report_processor, report):
    """
    Report processors should execute in component order and forward the final result.
    """
    replacement = HWPCReport(report.timestamp, report.sensor, report.target, {}, {'stage': 'first'})
    final_report = HWPCReport(report.timestamp, report.sensor, report.target, {}, {'stage': 'last'})
    last = Mock(spec=ReportProcessor, report_type=HWPCReport)
    second_processor = Mock(spec=Processor)
    second_processor.get_report_processors.return_value = (last,)
    processor_state.processors = (processor, second_processor)
    report_processor.process.return_value = replacement
    last.process.return_value = final_report

    StartMessageHandler(processor_state).handle(StartMessage())
    processor_state.handle_message(report)

    report_processor.process.assert_called_once_with(report)
    last.process.assert_called_once_with(replacement)
    for target in processor_state.actor.target_actors:
        target.send_data.assert_called_once_with(final_report)


def test_same_owner_report_processors_run_in_order(processor_state, processor, report_processor, report):
    """
    Same-type report processors from one component should execute in order.
    """
    processed_report = HWPCReport(report.timestamp, report.sensor, report.target, {}, {'stage': 'processed'})
    next_processor = Mock(spec=ReportProcessor, report_type=HWPCReport)
    processor.get_report_processors.return_value = (report_processor, next_processor)
    report_processor.process.return_value = processed_report
    next_processor.process.return_value = report

    StartMessageHandler(processor_state).handle(StartMessage())
    processor_state.handle_message(report)

    report_processor.process.assert_called_once_with(report)
    next_processor.process.assert_called_once_with(processed_report)
    for target in processor_state.actor.target_actors:
        target.send_data.assert_called_once_with(report)


def test_chain_drop_skips_next_processor_and_accepts_next_report(processor_state, report_processor, report):
    """
    Dropping a report should skip the next processor without stopping the chain.
    """
    next_processor = Mock(spec=ReportProcessor)
    report_processor.process.side_effect = [None, report]
    next_processor.process.return_value = report
    handler = ProcessorReportHandler(processor_state, (report_processor, next_processor))

    handler.handle(report)

    next_processor.process.assert_not_called()
    for target in processor_state.actor.target_actors:
        target.send_data.assert_not_called()

    handler.handle(report)

    next_processor.process.assert_called_once_with(report)
    for target in processor_state.actor.target_actors:
        target.send_data.assert_called_once_with(report)


def test_chain_failure_does_not_process_or_forward_partial_result(processor_state, report_processor, report):
    """
    Processing failures should propagate without executing later stages.
    """
    last = Mock(spec=ReportProcessor, report_type=HWPCReport)
    report_processor.process.side_effect = RuntimeError('processing failed')
    handler = ProcessorReportHandler(processor_state, (report_processor, last))

    with pytest.raises(RuntimeError, match='processing failed'):
        handler.handle(report)

    last.process.assert_not_called()
    for target in processor_state.actor.target_actors:
        target.send_data.assert_not_called()


def test_multiple_processors_initialize_and_teardown_in_order(processor_state, processor):
    """
    Components should initialize in declaration order and tear down in reverse order.
    """
    second_processor = Mock(spec=Processor)
    second_processor.get_report_processors.return_value = ()
    processor_state.processors = (processor, second_processor)
    lifecycle = Mock()
    lifecycle.attach_mock(processor, 'first')
    lifecycle.attach_mock(second_processor, 'second')

    processor_state.initialize()
    processor_state.teardown()

    assert lifecycle.mock_calls == [
        call.first.initialize(),
        call.first.get_report_processors(),
        call.second.initialize(),
        call.second.get_report_processors(),
        call.second.teardown(),
        call.first.teardown(),
    ]
