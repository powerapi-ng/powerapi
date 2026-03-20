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

import pytest

from powerapi.cli.generator import ModelNameDoesNotExist
from powerapi.cli.generator import PullerGenerator, DBActorGenerator, PusherGenerator, PreProcessorGenerator
from powerapi.database.csv import CSVInput, CSVOutput
from powerapi.database.json import JsonInput, JsonOutput
from powerapi.database.socket import Socket
from powerapi.exception import PowerAPIException
from powerapi.filter import BroadcastReportFilter
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.report import PowerReport, FormulaReport


def test_generate_puller_from_empty_config_dict_raise_an_exception():
    """
    Test that PullerGenerator raises a PowerAPIException when there is no input argument
    """
    conf = {}
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_several_pullers_from_config(several_inputs_outputs_stream_config):
    """
    Test that several inputs are correctly used to generate the related actors
    """
    for current_input in several_inputs_outputs_stream_config['input'].values():
        if current_input['type'] == 'csv':
            current_input['files'] = current_input['files'].split(',')

    generator = PullerGenerator(BroadcastReportFilter())
    pullers = generator.generate(several_inputs_outputs_stream_config)

    assert len(pullers) == len(several_inputs_outputs_stream_config['input'])

    for puller_name, current_puller_infos in several_inputs_outputs_stream_config['input'].items():
        assert puller_name in pullers
        assert isinstance(pullers[puller_name], PullerActor)

        db = pullers[puller_name].database

        if current_puller_infos['type'] == 'csv':
            assert isinstance(db, CSVInput)
            assert all(str(filepath) in current_puller_infos['files'] for filepath  in db.input_filepaths)
        elif current_puller_infos['type'] == 'socket':
            assert isinstance(db, Socket)
            assert db.listen_addr == (current_puller_infos['host'], current_puller_infos['port'])
        elif current_puller_infos['type'] == 'json':
            assert isinstance(db, JsonInput)
            assert str(db.input_filepath) == current_puller_infos['filepath']
        else:
            pytest.fail(f'Unsupported puller type: {current_puller_infos["type"]}')


def test_generate_puller_raise_exception_when_missing_arguments_in_socket_input(
        several_inputs_outputs_stream_socket_without_some_arguments_config):
    """
    Test that PullerGenerator raise a PowerAPIException when some arguments are missing for socket input
    """
    generator = PullerGenerator(BroadcastReportFilter())

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_socket_without_some_arguments_config)


def test_remove_model_factory_that_does_not_exist_on_a_DBActorGenerator_must_raise_ModelNameDoesNotExist():
    """
    Test that an exception is raised when a model factory that does not exist is erased
    """
    generator = DBActorGenerator('input')
    num_report_classes = len(generator.report_classes)

    with pytest.raises(ModelNameDoesNotExist):
        generator.remove_report_class('model')

    assert len(generator.report_classes) == num_report_classes


def test_remove_hwpc_report_model_and_generate_puller_from_a_config_using_model(several_inputs_outputs_stream_config):
    """
    PullerGenerator should raise an exception when the model of an input is not defined.
    """
    generator = PullerGenerator(BroadcastReportFilter())
    generator.remove_report_class('HWPCReport')

    with pytest.raises(PowerAPIException):
        _ = generator.generate(several_inputs_outputs_stream_config)


def test_remove_csv_database_factory_and_generate_puller_from_a_config_using_type(several_inputs_outputs_stream_config):
    """
    PullerGenerator should raise an exception when the database of an input is not defined.
    """
    generator = PullerGenerator(BroadcastReportFilter())
    generator.remove_db_factory('csv')

    with pytest.raises(PowerAPIException):
        _ = generator.generate(several_inputs_outputs_stream_config)


def test_generate_pusher_from_empty_config_dict_raise_an_exception():
    """
    Test that PusherGenerator raise an exception when there is no output argument
    """
    conf = {}
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_several_pushers_from_config(several_inputs_outputs_stream_config):
    """
    Test that several outputs are correctly used to generate the related actors

    """
    generator = PusherGenerator()
    pushers = generator.generate(several_inputs_outputs_stream_config)

    assert len(pushers) == len(several_inputs_outputs_stream_config['output'])

    for pusher_name, current_pusher_infos in several_inputs_outputs_stream_config['output'].items():
        assert pusher_name in pushers
        assert isinstance(pushers[pusher_name], PusherActor)

        db = pushers[pusher_name].database
        pusher_type = current_pusher_infos['type']

        if pusher_type == 'csv':
            assert isinstance(db, CSVOutput)
            assert str(db.output_directory) == current_pusher_infos['directory']
        elif pusher_type == 'json':
            assert isinstance(db, JsonOutput)
            assert str(db.output_filepath) == current_pusher_infos['filepath']
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


def test_generate_pre_processor_from_empty_config_dict_raise_an_exception():
    """
    Test that PreProcessGenerator raise an exception when there is no processor argument
    """
    conf = {}
    generator = PreProcessorGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)
