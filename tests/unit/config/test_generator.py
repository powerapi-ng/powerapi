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

import logging
from copy import deepcopy

import pytest

from powerapi.config.generator import (
    PreProcessorGenerator,
    PullerGenerator,
    PusherGenerator,
)
from powerapi.database.csv.driver import CSVInputFactory, CSVOutputFactory
from powerapi.database.json.driver import JsonInputFactory, JsonOutputFactory
from powerapi.database.socket.driver import SocketInputFactory
from powerapi.exception import ConfigurationError, PowerAPIException
from powerapi.filter import BroadcastReportFilter
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.report import FormulaReport, HWPCReport, PowerReport


def _unavailable_factory(_: dict):
    """
    Simulate a component factory whose optional dependency is unavailable.
    """
    raise ImportError


def test_generate_puller_from_empty_config_dict_raise_an_exception():
    """
    Test that PullerGenerator raises a PowerAPIException when there is no input argument.
    """
    conf = {}
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


@pytest.mark.parametrize('input_type', ['csv', 'json'])
def test_generate_file_puller_in_stream_mode_raise_an_exception(several_inputs_outputs_stream_config, input_type):
    """
    Test that PullerGenerator rejects input types that do not support stream mode.
    """
    config = deepcopy(several_inputs_outputs_stream_config)
    config['input'] = {name: value for name, value in config['input'].items() if value['type'] == input_type}
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(ConfigurationError) as raised_exception:
        generator.generate(config)

    assert raised_exception.value.path == 'stream'
    assert raised_exception.value.reason == f'Stream mode cannot be used with a {input_type} input'


def test_generate_several_pullers_from_config(several_inputs_outputs_postmortem_config):
    """
    Test that several inputs are correctly used to generate the related actors.
    """
    generator = PullerGenerator(BroadcastReportFilter())
    pullers = generator.generate(several_inputs_outputs_postmortem_config)

    assert len(pullers) == len(several_inputs_outputs_postmortem_config['input'])

    for puller_name, current_puller_infos in several_inputs_outputs_postmortem_config['input'].items():
        assert puller_name in pullers
        assert isinstance(pullers[puller_name], PullerActor)

        db_factory = pullers[puller_name].database_factory

        if current_puller_infos['type'] == 'csv':
            assert isinstance(db_factory, CSVInputFactory)
            assert db_factory.input_files == current_puller_infos['files']
        elif current_puller_infos['type'] == 'socket':
            assert isinstance(db_factory, SocketInputFactory)
            assert db_factory.host == current_puller_infos['host']
            assert db_factory.port == current_puller_infos['port']
        elif current_puller_infos['type'] == 'json':
            assert isinstance(db_factory, JsonInputFactory)
            assert db_factory.output_filepath == current_puller_infos['filepath']
        else:
            pytest.fail(f'Unsupported puller type: {current_puller_infos["type"]}')


def test_generate_streaming_puller_preserves_runtime_settings(several_inputs_outputs_stream_config):
    """
    Test that a streaming puller receives its filter, stream mode, and logging level.
    """
    config = deepcopy(several_inputs_outputs_stream_config)
    config['input'] = {'puller3': config['input']['puller3']}
    report_filter = BroadcastReportFilter()

    puller = PullerGenerator(report_filter).generate(config)['puller3']

    assert puller.report_filter is report_filter
    assert puller.stream_mode is True
    assert puller.logging_level == logging.DEBUG


def test_generate_puller_with_registered_report_model(several_inputs_outputs_postmortem_config):
    """
    Test that a registered report model is resolved when generating a puller.
    """
    config = deepcopy(several_inputs_outputs_postmortem_config)
    config['input'] = {'puller2': config['input']['puller2']}
    config['input']['puller2']['model'] = 'CustomReport'
    generator = PullerGenerator(BroadcastReportFilter())
    generator.add_report_class('CustomReport', HWPCReport)

    puller = generator.generate(config)['puller2']

    assert puller.database_factory.report_type is HWPCReport


def test_register_existing_report_model_raises_value_error():
    """
    Test that a report model cannot be registered more than once.
    """
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(ValueError, match='Report model "HWPCReport" is already registered'):
        generator.add_report_class('HWPCReport', HWPCReport)


def test_register_existing_database_type_raises_value_error():
    """
    Test that a database type cannot be registered more than once.
    """
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(ValueError, match='Database type "csv" is already registered'):
        generator.add_db_factory('csv', generator.database_factories['csv'])


def test_generate_puller_with_unknown_report_model_raises_an_exception(several_inputs_outputs_postmortem_config):
    """
    PullerGenerator should raise an exception when the model of an input is not defined.
    """
    config = deepcopy(several_inputs_outputs_postmortem_config)
    next(iter(config['input'].values()))['model'] = 'UnknownReport'
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(PowerAPIException, match='Configuration error: Unknown report model "UnknownReport"'):
        generator.generate(config)


def test_generate_puller_with_unknown_database_type_raises_an_exception(several_inputs_outputs_postmortem_config):
    """
    PullerGenerator should raise an exception when the database of an input is not defined.
    """
    config = deepcopy(several_inputs_outputs_postmortem_config)
    next(iter(config['input'].values()))['type'] = 'unknown'
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(PowerAPIException, match='Configuration error: Invalid database type: unknown'):
        generator.generate(config)


def test_generate_puller_with_unavailable_database_dependency_raises_an_exception(several_inputs_outputs_postmortem_config):
    """
    Test that a missing database dependency is reported as a configuration error.
    """
    config = deepcopy(several_inputs_outputs_postmortem_config)
    config['input'] = {'puller2': config['input']['puller2']}
    config['input']['puller2']['type'] = 'unavailable'
    generator = PullerGenerator(BroadcastReportFilter())
    generator.add_db_factory('unavailable', _unavailable_factory)

    with pytest.raises(PowerAPIException, match='Dependencies for unavailable database are not installed'):
        generator.generate(config)


def test_generate_does_not_modify_configuration(several_inputs_outputs_postmortem_config):
    """
    Test that generating pullers and pushers repeatedly preserves the canonical configuration.
    """
    expected = deepcopy(several_inputs_outputs_postmortem_config)
    puller_generator = PullerGenerator(BroadcastReportFilter())
    pusher_generator = PusherGenerator()

    puller_generator.generate(several_inputs_outputs_postmortem_config)
    pusher_generator.generate(several_inputs_outputs_postmortem_config)
    puller_generator.generate(several_inputs_outputs_postmortem_config)
    pusher_generator.generate(several_inputs_outputs_postmortem_config)

    assert several_inputs_outputs_postmortem_config == expected


def test_generate_pusher_from_empty_config_dict_raises_an_exception():
    """
    Test that PusherGenerator raises an exception when there is no output argument.
    """
    conf = {}
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_several_pushers_from_config(several_inputs_outputs_stream_config):
    """
    Test that several outputs are correctly used to generate the related actors.

    """
    generator = PusherGenerator()
    pushers = generator.generate(several_inputs_outputs_stream_config)

    assert len(pushers) == len(several_inputs_outputs_stream_config['output'])

    for pusher_name, current_pusher_infos in several_inputs_outputs_stream_config['output'].items():
        assert pusher_name in pushers
        assert isinstance(pushers[pusher_name], PusherActor)

        db_factory = pushers[pusher_name].database_factory
        pusher_type = current_pusher_infos['type']

        if pusher_type == 'csv':
            assert isinstance(db_factory, CSVOutputFactory)
            assert db_factory.output_directory == current_pusher_infos['directory']
        elif pusher_type == 'json':
            assert isinstance(db_factory, JsonOutputFactory)
            assert db_factory.output_filepath == current_pusher_infos['filepath']
        else:
            pytest.fail(f'Unsupported pusher type: {pusher_type}')


def test_generate_pusher_report_type_to_actor_mapping(single_input_multiple_outputs_with_different_report_type):
    """
    Test generating a report type to actor mapping from a configuration having multiple outputs for different report types.
    """
    config = single_input_multiple_outputs_with_different_report_type
    generator = PusherGenerator()
    actors = generator.generate(config)
    report_mapping = generator.generate_report_mapping(config, actors)

    assert set(report_mapping.keys()) == {PowerReport, FormulaReport}
    assert [proxy.actor_name for proxy in report_mapping[PowerReport]] == ['powerrep1', 'powerrep2']
    assert [proxy.actor_type for proxy in report_mapping[PowerReport]] == [PusherActor, PusherActor]
    assert [proxy.actor_name for proxy in report_mapping[FormulaReport]] == ['formularep']
    assert [proxy.actor_type for proxy in report_mapping[FormulaReport]] == [PusherActor]


def test_generate_pusher_report_mapping_without_output_group_raises_an_exception():
    """
    Test that report mapping requires the output component group.
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException, match='Configuration error: Component "output" is not defined'):
        generator.generate_report_mapping({}, {})


def test_generate_pusher_report_mapping_with_missing_actor_raises_an_exception():
    """
    Test that report mapping rejects an output without a generated actor.
    """
    config = {'output': {'missing': {'model': 'PowerReport'}}}
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException, match='Actor "missing" is not defined'):
        generator.generate_report_mapping(config, {})


def test_generate_pre_processor_from_empty_config_dict_raises_an_exception():
    """
    Test that PreProcessGenerator raises an exception when there is no processor argument.
    """
    conf = {}
    generator = PreProcessorGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_register_existing_processor_type_raises_value_error():
    """
    Test that a processor type cannot be registered more than once.
    """
    generator = PreProcessorGenerator()

    with pytest.raises(ValueError, match='Processor type "kubernetes" is already registered'):
        generator.add_processor_factory('kubernetes', generator.processor_factories['kubernetes'])


def test_generate_unknown_processor_type_raises_an_exception():
    """
    Test that generating an unknown processor type raises a configuration error.
    """
    config = {'verbose': False, 'pre-processor': {'processor': {'type': 'unknown'}}}

    with pytest.raises(PowerAPIException, match='Configuration error: Invalid processor type: unknown'):
        PreProcessorGenerator().generate(config)


def test_generate_processor_with_unavailable_dependency_raises_an_exception():
    """
    Test that a missing processor dependency is reported as a configuration error.
    """
    config = {'verbose': False, 'pre-processor': {'processor': {'type': 'unavailable'}}}
    generator = PreProcessorGenerator()
    generator.add_processor_factory('unavailable', _unavailable_factory)

    with pytest.raises(PowerAPIException, match='Dependencies for unavailable processor are not installed'):
        generator.generate(config)
