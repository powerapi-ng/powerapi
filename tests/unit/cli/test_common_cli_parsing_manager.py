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

import pytest

from powerapi.cli.common_cli_parsing_manager import CommonCLIParsingManager, PullerConfigParsingManager, \
    PusherConfigParsingManager, PreProcessorConfigParsingManager, generate_env_prefix
from powerapi.cli.config_parser import store_true
from powerapi.exception import NoNameSpecifiedForSubgroupException


def test_generate_env_prefix_with_no_component():
    """
    Test environment variable prefix generation with only the root prefix.
    """
    assert generate_env_prefix() == 'POWERAPI_'


def test_generate_env_prefix_with_one_component():
    """
    Test environment variable prefix generation with one component.
    """
    assert generate_env_prefix('INPUT') == 'POWERAPI_INPUT_'


def test_generate_env_prefix_with_several_components():
    """
    Test environment variable prefix generation with several components.
    """
    assert generate_env_prefix('PRE', 'PROCESSOR') == 'POWERAPI_PRE_PROCESSOR_'


def test_generate_env_prefix_normalizes_case():
    """
    Test that environment variable prefix generation normalizes components to uppercase.
    """
    assert generate_env_prefix('input') == 'POWERAPI_INPUT_'


def test_generate_env_prefix_strips_blank_components():
    """
    Test that environment variable prefix generation ignores blank components.
    """
    assert generate_env_prefix('', 'INPUT') == 'POWERAPI_INPUT_'


def test_generate_env_prefix_with_custom_root_prefix():
    """
    Test environment variable prefix generation with a custom root prefix.
    """
    assert generate_env_prefix('INPUT', root_prefix='MYAPP') == 'MYAPP_INPUT_'


def test_puller_config_parser_registers_shared_name_argument():
    """
    Test that PullerConfigParsingManager registers the shared subgroup name argument.
    """
    parser = PullerConfigParsingManager('pytest')
    name_argument = parser.cli_parser.get_arguments()['name']

    assert name_argument.names == ['n', 'name']
    assert name_argument.is_mandatory is False


def test_puller_config_parser_registers_default_model_argument():
    """
    Test that PullerConfigParsingManager registers the default report model argument.
    """
    parser = PullerConfigParsingManager('pytest')
    model_argument = parser.cli_parser.get_arguments()['model']

    assert model_argument.names == ['m', 'model']
    assert model_argument.default_value == 'HWPCReport'


def test_pusher_config_parser_registers_shared_name_argument():
    """
    Test that PusherConfigParsingManager registers the shared subgroup name argument.
    """
    parser = PusherConfigParsingManager('pytest')
    name_argument = parser.cli_parser.get_arguments()['name']

    assert name_argument.names == ['n', 'name']
    assert name_argument.is_mandatory is False


def test_pusher_config_parser_registers_default_model_argument():
    """
    Test that PusherConfigParsingManager registers the default report model argument.
    """
    parser = PusherConfigParsingManager('pytest')
    model_argument = parser.cli_parser.get_arguments()['model']

    assert model_argument.names == ['m', 'model']
    assert model_argument.default_value == 'PowerReport'


def test_pre_processor_config_parser_registers_shared_name_argument():
    """
    Test that PreProcessorConfigParsingManager registers the shared subgroup name argument.
    """
    parser = PreProcessorConfigParsingManager('pytest')
    name_argument = parser.cli_parser.get_arguments()['name']

    assert name_argument.names == ['n', 'name']
    assert name_argument.is_mandatory is False


def test_pre_processor_config_parser_registers_mandatory_puller_argument():
    """
    Test that PreProcessorConfigParsingManager registers a mandatory puller argument.
    """
    parser = PreProcessorConfigParsingManager('pytest')
    puller_argument = parser.cli_parser.get_arguments()['puller']

    assert puller_argument.names == ['p', 'puller']
    assert puller_argument.is_mandatory is True


def test_common_cli_manager_registers_root_environment_prefix():
    """
    Test that CommonCLIParsingManager registers the root PowerAPI environment prefix.
    """
    parser_manager = CommonCLIParsingManager()

    assert parser_manager.cli_parser.arguments_prefix == ['POWERAPI_']


def test_common_cli_manager_registers_subgroup_environment_prefixes():
    """
    Test that CommonCLIParsingManager registers every subgroup environment prefix.
    """
    parser_manager = CommonCLIParsingManager()

    assert parser_manager.cli_parser.get_groups_prefixes() == [
        'POWERAPI_INPUT_',
        'POWERAPI_OUTPUT_',
        'POWERAPI_PRE_PROCESSOR_',
        'POWERAPI_POST_PROCESSOR_',
    ]


def test_common_cli_manager_registers_top_level_subgroups():
    """
    Test that CommonCLIParsingManager registers every top-level subgroup.
    """
    parser_manager = CommonCLIParsingManager()

    assert set(parser_manager.cli_parser.subgroup_parsers) == {
        'input',
        'output',
        'pre-processor',
        'post-processor',
    }


def test_common_cli_manager_registers_input_parsers():
    """
    Test that CommonCLIParsingManager registers every built-in input parser.
    """
    parser_manager = CommonCLIParsingManager()

    assert set(parser_manager.subparser['input']) == {
        'mongodb',
        'socket',
        'csv',
        'json',
    }


def test_common_cli_manager_registers_output_parsers():
    """
    Test that CommonCLIParsingManager registers every built-in output parser.
    """
    parser_manager = CommonCLIParsingManager()

    assert set(parser_manager.subparser['output']) == {
        'mongodb',
        'prometheus',
        'csv',
        'json',
        'opentsdb',
        'influxdb2',
    }


def test_common_cli_manager_registers_pre_processor_parsers():
    """
    Test that CommonCLIParsingManager registers every built-in pre-processor parser.
    """
    parser_manager = CommonCLIParsingManager()

    assert set(parser_manager.subparser['pre-processor']) == {
        'k8s',
        'openstack',
    }


def test_common_cli_manager_registers_verbose_argument():
    """
    Test that CommonCLIParsingManager registers the verbose root argument.
    """
    parser_manager = CommonCLIParsingManager()
    verbose_argument = parser_manager.cli_parser.get_arguments()['verbose']

    assert verbose_argument.names == ['v', 'verbose']
    assert verbose_argument.is_flag is True
    assert verbose_argument.action is store_true
    assert verbose_argument.default_value is False


def test_common_cli_manager_registers_stream_argument():
    """
    Test that CommonCLIParsingManager registers the stream root argument.
    """
    parser_manager = CommonCLIParsingManager()
    stream_argument = parser_manager.cli_parser.get_arguments()['stream']

    assert stream_argument.names == ['s', 'stream']
    assert stream_argument.is_flag is True
    assert stream_argument.action is store_true
    assert stream_argument.default_value is False


def test_common_cli_manager_validates_output_config_without_name():
    """
    Test that output config validation can use the output key as the pusher name.
    """
    parser_manager = CommonCLIParsingManager()
    config = {
        'output': {
            'powerrep': {
                'model': 'PowerReport',
                'type': 'json',
                'filepath': '/tmp/powerapi-output.jsonl',
            },
        },
    }

    result = parser_manager.validate(config)

    assert result['output']['powerrep']['type'] == 'json'
    assert result['output']['powerrep']['model'] == 'PowerReport'
    assert result['output']['powerrep']['filepath'] == '/tmp/powerapi-output.jsonl'
    assert result['output']['powerrep']['compression'] == 'auto'


def test_common_cli_manager_requires_name_for_cli_subgroup():
    """
    Test that CLI subgroup parsing still requires -n/--name.
    """
    parser_manager = CommonCLIParsingManager()

    with pytest.raises(NoNameSpecifiedForSubgroupException):
        parser_manager._parse_cli([
            '--output', 'json',
            '--filepath', '/tmp/powerapi-output.jsonl',
        ])


def test_common_cli_manager_parse_cli_configuration():
    """
    Test that CommonCLIParsingManager parses a representative CLI configuration.
    """
    parser_manager = CommonCLIParsingManager()

    result = parser_manager._parse_cli([
        '--verbose',
        '--input', 'csv',
        '--name', 'pytest-puller',
        '--files', 'a.csv,b.csv',
        '--output', 'json',
        '--name', 'pytest-pusher',
        '--filepath', '/tmp/pytest-powerapi.jsonl'
    ])

    assert result['verbose'] is True
    assert result['input']['pytest-puller']['type'] == 'csv'
    assert result['input']['pytest-puller']['files'] == ['a.csv', 'b.csv']
    assert result['output']['pytest-pusher']['type'] == 'json'
    assert result['output']['pytest-pusher']['filepath'] == '/tmp/pytest-powerapi.jsonl'
