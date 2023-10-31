# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

import os
import re
from re import Pattern

import pytest

from powerapi.cli.generator import PullerGenerator, DBActorGenerator, PusherGenerator, ProcessorGenerator, \
    MonitorGenerator, MONITOR_NAME_SUFFIX, LISTENER_ACTOR_KEY, PreProcessorGenerator
from powerapi.cli.generator import ModelNameDoesNotExist
from powerapi.processor.pre.k8s.k8s_monitor import K8sMonitorAgent
from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorActor, TIME_INTERVAL_DEFAULT_VALUE, \
    TIMEOUT_QUERY_DEFAULT_VALUE
from powerapi.processor.pre.libvirt.libvirt_pre_processor_actor import LibvirtPreProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.database import MongoDB, CsvDB, SocketDB, InfluxDB, PrometheusDB, InfluxDB2
from powerapi.exception import PowerAPIException


####################
# PULLER GENERATOR #
####################
def test_generate_puller_from_empty_config_dict_raise_an_exception():
    """
    Test that PullerGenerator raises a PowerAPIException when there is no input argument
    """
    conf = {}
    generator = PullerGenerator(report_filter=None, report_modifier_list=[])

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_puller_from_mongo_basic_config(mongodb_input_output_stream_config):
    """
    Test that generation for mongodb puller from a config with a mongodb input works correctly
    """
    generator = PullerGenerator(None, [])

    pullers = generator.generate(mongodb_input_output_stream_config)

    assert len(pullers) == 1
    assert 'one_puller' in pullers
    puller = pullers['one_puller']
    assert isinstance(puller, PullerActor)

    db = puller.state.database

    assert isinstance(db, MongoDB)
    assert db.uri == mongodb_input_output_stream_config['input']['one_puller']['uri']
    assert db.db_name == mongodb_input_output_stream_config['input']['one_puller']['db']
    assert db.collection_name == mongodb_input_output_stream_config['input']['one_puller']['collection']


def test_generate_several_pullers_from_config(several_inputs_outputs_stream_config):
    """
    Test that several inputs are correctly used to generate the related actors

    """
    for _, current_input in several_inputs_outputs_stream_config['input'].items():
        if current_input['type'] == 'csv':
            current_input['files'] = current_input['files'].split(',')
    generator = PullerGenerator(report_filter=None, report_modifier_list=[])
    pullers = generator.generate(several_inputs_outputs_stream_config)

    assert len(pullers) == len(several_inputs_outputs_stream_config['input'])

    for puller_name, current_puller_infos in several_inputs_outputs_stream_config['input'].items():
        assert puller_name in pullers
        assert isinstance(pullers[puller_name], PullerActor)

        db = pullers[puller_name].state.database

        if current_puller_infos['type'] == 'mongodb':
            assert isinstance(db, MongoDB)
            assert db.uri == current_puller_infos['uri']
            assert db.db_name == current_puller_infos['db']
            assert db.collection_name == current_puller_infos['collection']

        elif current_puller_infos['type'] == 'csv':
            assert isinstance(db, CsvDB)
            assert all(file in db.filenames for file in current_puller_infos['files'])

        elif current_puller_infos['type'] == 'socket':
            assert isinstance(db, SocketDB)
            assert db.port == current_puller_infos['port']

        else:
            assert False


def test_generate_puller_raise_exception_when_missing_arguments_in_mongo_input(
        several_inputs_outputs_stream_mongo_without_some_arguments_config):
    """
    Test that PullerGenerator raise a PowerAPIException when some arguments are missing for mongo input
    """
    generator = PullerGenerator(report_filter=None, report_modifier_list=[])

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_mongo_without_some_arguments_config)


def test_generate_puller_when_missing_arguments_in_csv_input_generate_related_actors(
        several_inputs_outputs_stream_csv_without_some_arguments_config):
    """
    Test that PullerGenerator generates the csv related actors even if there are some missing arguments
    """
    generator = PullerGenerator(report_filter=None, report_modifier_list=[])

    pullers = generator.generate(several_inputs_outputs_stream_csv_without_some_arguments_config)

    assert len(pullers) == len(several_inputs_outputs_stream_csv_without_some_arguments_config['input'])

    for puller_name, current_puller_infos in several_inputs_outputs_stream_csv_without_some_arguments_config['input']. \
            items():

        if current_puller_infos['type'] == 'csv':
            assert puller_name in pullers
            assert isinstance(pullers[puller_name], PullerActor)

            db = pullers[puller_name].state.database
            assert isinstance(db, CsvDB)
            assert isinstance(db.filenames, list)
            assert len(db.filenames) == 0
            assert db.current_path == os.getcwd() + '/'


def test_generate_puller_raise_exception_when_missing_arguments_in_socket_input(
        several_inputs_outputs_stream_socket_without_some_arguments_config):
    """
    Test that PullerGenerator raise a PowerAPIException when some arguments are missing for socket input
    """
    generator = PullerGenerator(report_filter=None, report_modifier_list=[])

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_socket_without_some_arguments_config)


#########################
# DBActorGenerator Test #
#########################
def test_remove_model_factory_that_does_not_exist_on_a_DBActorGenerator_must_raise_ModelNameDoesNotExist():
    """
    Test that an exception is raised when a model factory that does not exist is erased
    """
    generator = DBActorGenerator('input')

    assert len(generator.report_classes) == 5

    with pytest.raises(ModelNameDoesNotExist):
        generator.remove_report_class('model')

    assert len(generator.report_classes) == 5


def test_remove_HWPCReport_model_and_generate_puller_from_a_config_with_hwpc_report_model_raise_an_exception(
        mongodb_input_output_stream_config):
    """
    Test that PullGenerator raises PowerAPIException when the model class is not defined
    """
    generator = PullerGenerator(None, [])
    generator.remove_report_class('HWPCReport')
    with pytest.raises(PowerAPIException):
        _ = generator.generate(mongodb_input_output_stream_config)


def test_remove_mongodb_factory_and_generate_puller_from_a_config_with_mongodb_input_must_call_sys_exit_(
        mongodb_input_output_stream_config):
    """
    Test that PullGenerator raises a PowerAPIException when an input type is not defined
    """
    generator = PullerGenerator(None, [])
    generator.remove_db_factory('mongodb')
    with pytest.raises(PowerAPIException):
        _ = generator.generate(mongodb_input_output_stream_config)


#########################
# PusherGenerator Test #
#########################
def test_generate_pusher_from_empty_config_dict_raise_an_exception():
    """
    Test that PusherGenerator raise an exception when there is no output argument
    """
    conf = {}
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_pusher_from_mongo_basic_config(mongodb_input_output_stream_config):
    """
    Test that generation for mongodb puller from a config with a mongodb input works correctly
    """
    generator = PusherGenerator()

    pushers = generator.generate(mongodb_input_output_stream_config)

    assert len(pushers) == 1
    assert 'one_pusher' in pushers
    pusher = pushers['one_pusher']
    assert isinstance(pusher, PusherActor)

    db = pusher.state.database

    assert isinstance(db, MongoDB)
    assert db.uri == mongodb_input_output_stream_config['output']['one_pusher']['uri']
    assert db.db_name == mongodb_input_output_stream_config['output']['one_pusher']['db']
    assert db.collection_name == mongodb_input_output_stream_config['output']['one_pusher']['collection']


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

        db = pushers[pusher_name].state.database
        pusher_type = current_pusher_infos['type']

        if pusher_type == 'mongodb':
            assert isinstance(db, MongoDB)
            assert db.uri == current_pusher_infos['uri']
            assert db.db_name == current_pusher_infos['db']
            assert db.collection_name == current_pusher_infos['collection']

        elif pusher_type == 'influxdb':
            assert isinstance(db, InfluxDB)
            assert db.uri == current_pusher_infos['uri']
            assert db.db_name == current_pusher_infos['db']
            assert db.port == current_pusher_infos['port']

        elif pusher_type == 'prom':
            assert isinstance(db, PrometheusDB)
            assert db.address == current_pusher_infos['uri']
            assert db.port == current_pusher_infos['port']

        elif pusher_type == 'csv':
            assert isinstance(db, CsvDB)
            assert db.current_path == current_pusher_infos['directory'] + '/'

        elif pusher_type == 'influxdb2':
            assert isinstance(db, InfluxDB2)
            assert db.uri == current_pusher_infos['uri'] + ':' + str(current_pusher_infos['port'])
            assert db.bucket_name == current_pusher_infos['db']
            assert db.org == current_pusher_infos['org']
            assert db.tags == current_pusher_infos['tags'].split(',')
            assert db.token == current_pusher_infos['token']

        elif pusher_type == 'opentsdb':
            assert db.port == current_pusher_infos['port']
            assert db.host == current_pusher_infos['uri']
            assert db.metric_name == current_pusher_infos['metric_name']

        elif pusher_type == 'virtiofs':
            assert db.vm_name_regexp == re.compile(current_pusher_infos['vm_name_regexp'])
            assert db.root_directory_name == current_pusher_infos['root_directory_name']
            assert db.vm_directory_name_prefix == current_pusher_infos['vm_directory_name_prefix']
            assert db.vm_directory_name_suffix == current_pusher_infos['vm_directory_name_suffix']

        elif pusher_type == 'filedb':
            assert db.filename == current_pusher_infos['filename']

        else:
            assert False


def test_generate_pusher_raise_exception_when_missing_arguments_in_mongo_output(
        several_inputs_outputs_stream_mongo_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for mongo output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_mongo_without_some_arguments_config)


def test_generate_pusher_raise_exception_when_missing_arguments_in_influx_output(
        several_inputs_outputs_stream_influx_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for influx output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_influx_without_some_arguments_config)


def test_generate_pusher_raise_exception_when_missing_arguments_in_prometheus_output(
        several_inputs_outputs_stream_prometheus_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for prometheus output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_prometheus_without_some_arguments_config)


def test_generate_pusher_raise_exception_when_missing_arguments_in_opentsdb_output(
        several_inputs_outputs_stream_opentsdb_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for opentsdb output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_opentsdb_without_some_arguments_config)


def test_generate_pusher_raise_exception_when_missing_arguments_in_virtiofs_output(
        several_inputs_outputs_stream_virtiofs_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for virtiofs output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_virtiofs_without_some_arguments_config)


def test_generate_pusher_raise_exception_when_missing_arguments_in_filedb_output(
        several_inputs_outputs_stream_filedb_without_some_arguments_config):
    """
    Test that PusherGenerator raises a PowerAPIException when some arguments are missing for filedb output
    """
    generator = PusherGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_inputs_outputs_stream_filedb_without_some_arguments_config)


def test_generate_pusher_when_missing_arguments_in_csv_output_generate_related_actors(
        several_inputs_outputs_stream_csv_without_some_arguments_config):
    """
    Test that PusherGenerator generates the csv related actors even if there are some missing arguments
    """
    generator = PusherGenerator()
    generation_checked = False

    pushers = generator.generate(several_inputs_outputs_stream_csv_without_some_arguments_config)

    assert len(pushers) == len(several_inputs_outputs_stream_csv_without_some_arguments_config['output'])

    for pusher_name, current_pusher_infos in several_inputs_outputs_stream_csv_without_some_arguments_config['output']. \
            items():
        pusher_type = current_pusher_infos['type']
        if pusher_type == 'csv':
            assert pusher_name in pushers
            assert isinstance(pushers[pusher_name], PusherActor)

            db = pushers[pusher_name].state.database
            assert isinstance(db, CsvDB)
            assert isinstance(db.filenames, list)
            assert len(db.filenames) == 0
            assert db.current_path == os.getcwd() + '/'
            generation_checked = True

    assert generation_checked


################################
# PreProcessorActorGenerator Test #
################################
def test_generate_pre_processor_from_empty_config_dict_raise_an_exception():
    """
    Test that PreProcessGenerator raise an exception when there is no processor argument
    """
    conf = {}
    generator = PreProcessorGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(conf)


def test_generate_pre_processor_from_libvirt_config(libvirt_pre_processor_config):
    """
    Test that generation for libvirt pre-processor from a config works correctly
    """
    generator = PreProcessorGenerator()

    processors = generator.generate(libvirt_pre_processor_config)

    assert len(processors) == len(libvirt_pre_processor_config['pre-processor'])
    assert 'my_processor' in processors
    processor = processors['my_processor']

    assert isinstance(processor, LibvirtPreProcessorActor)

    assert processor.state.daemon_uri is None
    assert isinstance(processor.state.regexp, Pattern)


def test_generate_several_libvirt_pre_processors_from_config(several_libvirt_pre_processors_config):
    """
    Test that several libvirt pre-processors are correctly generated
    """
    generator = PreProcessorGenerator()

    processors = generator.generate(several_libvirt_pre_processors_config)

    assert len(processors) == len(several_libvirt_pre_processors_config['pre-processor'])

    for processor_name, current_processor_infos in several_libvirt_pre_processors_config['pre-processor'].items():
        assert processor_name in processors
        assert isinstance(processors[processor_name], LibvirtPreProcessorActor)

        assert processors[processor_name].state.daemon_uri is None
        assert isinstance(processors[processor_name].state.regexp, Pattern)


def test_generate_libvirt_pre_processor_raise_exception_when_missing_arguments(
        several_libvirt_processors_without_some_arguments_config):
    """
     Test that PreProcessorGenerator raises a PowerAPIException when some arguments are missing for libvirt processor
     """
    generator = PreProcessorGenerator()

    with pytest.raises(PowerAPIException):
        generator.generate(several_libvirt_processors_without_some_arguments_config)


def check_k8s_pre_processor_infos(pre_processor: K8sPreProcessorActor, expected_pre_processor_info: dict):
    """
    Check that the infos related to a K8sMonitorAgentActor are correct regarding its related K8SProcessorActor
    """
    assert isinstance(pre_processor, K8sPreProcessorActor)

    assert pre_processor.state.k8s_api_mode == expected_pre_processor_info["k8s_api_mode"]
    assert pre_processor.state.time_interval == expected_pre_processor_info["time_interval"]
    assert pre_processor.state.timeout_query == expected_pre_processor_info["timeout_query"]
    assert len(pre_processor.state.target_actors) == 0
    assert len(pre_processor.state.target_actors_names) == 1
    assert pre_processor.state.target_actors_names[0] == expected_pre_processor_info["puller"]


def test_generate_pre_processor_from_k8s_config(k8s_pre_processor_config):
    """
    Test that generation for k8s processor from a config works correctly
    """
    generator = PreProcessorGenerator()
    processor_name = 'my_processor'

    processors = generator.generate(k8s_pre_processor_config)

    assert len(processors) == len(k8s_pre_processor_config['pre-processor'])
    assert processor_name in processors

    processor = processors[processor_name]

    check_k8s_pre_processor_infos(pre_processor=processor,
                                  expected_pre_processor_info=k8s_pre_processor_config["pre-processor"][processor_name])


def test_generate_several_k8s_pre_processors_from_config(several_k8s_pre_processors_config):
    """
    Test that several k8s pre-processors are correctly generated
    """
    generator = PreProcessorGenerator()

    processors = generator.generate(several_k8s_pre_processors_config)

    assert len(processors) == len(several_k8s_pre_processors_config['pre-processor'])

    for processor_name, current_processor_infos in several_k8s_pre_processors_config['pre-processor'].items():
        assert processor_name in processors

        processor = processors[processor_name]

        check_k8s_pre_processor_infos(pre_processor=processor, expected_pre_processor_info=current_processor_infos)


def test_generate_k8s_pre_processor_uses_default_values_with_missing_arguments(
        several_k8s_pre_processors_without_some_arguments_config):
    """
     Test that PreProcessorGenerator generates a pre-processor with default values when arguments are not defined
     """
    generator = PreProcessorGenerator()

    processors = generator.generate(several_k8s_pre_processors_without_some_arguments_config)

    expected_processor_info = {'k8s_api_mode': None, 'time_interval': TIME_INTERVAL_DEFAULT_VALUE,
                               'timeout_query': TIMEOUT_QUERY_DEFAULT_VALUE}

    assert len(processors) == len(several_k8s_pre_processors_without_some_arguments_config['pre-processor'])

    pre_processor_number = 1
    for pre_processor_name in several_k8s_pre_processors_without_some_arguments_config['pre-processor']:
        assert pre_processor_name in processors

        processor = processors[pre_processor_name]
        expected_processor_info['puller'] = 'my_puller_' + str(pre_processor_number)

        check_k8s_pre_processor_infos(pre_processor=processor, expected_pre_processor_info=expected_processor_info)

        pre_processor_number += 1


def check_k8s_monitor_infos(monitor: K8sMonitorAgent, associated_processor: K8sPreProcessorActor):
    """
    Check that the infos related to a K8sMonitorAgentActor are correct regarding its related K8SProcessorActor
    """

    assert isinstance(monitor, K8sMonitorAgent)

    assert monitor.concerned_actor_state.k8s_api_mode == associated_processor.state.k8s_api_mode

    assert monitor.concerned_actor_state.time_interval == associated_processor.state.time_interval

    assert monitor.concerned_actor_state.timeout_query == associated_processor.state.timeout_query

    assert monitor.concerned_actor_state.api_key == associated_processor.state.api_key

    assert monitor.concerned_actor_state.host == associated_processor.state.host


def test_generate_k8s_monitor_from_k8s_config(k8s_monitor_config):
    """
    Test that generation for k8s monitor from a processor config works correctly
    """
    generator = MonitorGenerator()
    monitor_name = 'my_processor' + MONITOR_NAME_SUFFIX

    monitors = generator.generate(k8s_monitor_config)

    assert len(monitors) == len(k8s_monitor_config)

    assert monitor_name in monitors

    monitor = monitors[monitor_name]

    check_k8s_monitor_infos(monitor=monitor,
                            associated_processor=k8s_monitor_config['monitor'][monitor_name][LISTENER_ACTOR_KEY])


def test_generate_several_k8s_monitors_from_config(several_k8s_monitors_config):
    """
    Test that several k8s monitors are correctly generated
    """
    generator = MonitorGenerator()

    monitors = generator.generate(several_k8s_monitors_config)

    assert len(monitors) == len(several_k8s_monitors_config['monitor'])

    for monitor_name, current_monitor_infos in several_k8s_monitors_config['monitor'].items():
        assert monitor_name in monitors

        monitor = monitors[monitor_name]

        check_k8s_monitor_infos(monitor=monitor, associated_processor=current_monitor_infos[LISTENER_ACTOR_KEY])


def test_generate_k8s_monitor_from_k8s_processors(k8s_pre_processors):
    """
    Test that generation for k8s monitor from a processor config works correctly
    """
    generator = MonitorGenerator()
    processor_name = 'my_processor'
    monitor_name = processor_name + MONITOR_NAME_SUFFIX

    monitors = generator.generate_from_processors(processors=k8s_pre_processors)

    assert len(monitors) == len(k8s_pre_processors)

    assert monitor_name in monitors

    monitor = monitors[monitor_name]

    check_k8s_monitor_infos(monitor=monitor,
                            associated_processor=k8s_pre_processors[processor_name])


def test_generate_several_k8s_monitors_from_processors(several_k8s_pre_processors):
    """
    Test that several k8s monitors are correctly generated
    """
    generator = MonitorGenerator()

    monitors = generator.generate_from_processors(processors=several_k8s_pre_processors)

    assert len(monitors) == len(several_k8s_pre_processors)

    for processor_name, processor in several_k8s_pre_processors.items():
        monitor_name = processor_name + MONITOR_NAME_SUFFIX
        assert monitor_name in monitors

        monitor = monitors[monitor_name]

        check_k8s_monitor_infos(monitor=monitor, associated_processor=processor)
