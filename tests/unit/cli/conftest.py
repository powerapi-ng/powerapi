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

from tests.utils.cli.base_config_parser import load_configuration_from_json_file


@pytest.fixture
def several_inputs_outputs_stream_config():
    """
    Configuration with several inputs and outputs and stream mode enabled
    """
    return load_configuration_from_json_file('several_inputs_outputs_stream_mode_enabled_configuration.json')


@pytest.fixture
def several_inputs_outputs_stream_socket_without_some_arguments_config(several_inputs_outputs_stream_config):
    """
    Configuration with a socket input missing a required argument.
    """
    for current_input in several_inputs_outputs_stream_config['input'].values():
        if current_input['type'] == 'socket':
            current_input.pop('port')

    return several_inputs_outputs_stream_config


@pytest.fixture
def several_inputs_outputs_postmortem_config(several_inputs_outputs_stream_config):
    """
    Configuration with several inputs and outputs and stream mode disabled.
    """
    several_inputs_outputs_stream_config['stream'] = False
    return several_inputs_outputs_stream_config


@pytest.fixture
def single_input_multiple_outputs_with_different_report_type():
    """
    Configuration with several inputs and outputs and stream mode enabled
    """
    return load_configuration_from_json_file('single_input_multiple_outputs_with_different_report_type_configuration.json')


@pytest.fixture
def output_input_configuration():
    """
    Return a dictionary containing bindings with a processor
    """
    return load_configuration_from_json_file(file_name='output_input_configuration.json')


@pytest.fixture(params=['k8s_pre_processor_complete_configuration.json'])
def pre_processor_complete_configuration(request):
    """
    Return a dictionary containing a configuration with pre-processor
    """
    return load_configuration_from_json_file(file_name=request.param)


@pytest.fixture
def empty_pre_processor_config(pre_processor_complete_configuration):
    """
    Return a configuration with bindings but without processors
    """

    pre_processor_complete_configuration.pop('pre-processor')

    return pre_processor_complete_configuration


@pytest.fixture(params=['k8s_pre_processor_with_non_existing_puller_configuration.json'])
def pre_processor_with_unexisting_puller_configuration(request):
    """
    Return a dictionary containing a pre-processor with a puller that doesn't exist
    """
    return load_configuration_from_json_file(request.param)
