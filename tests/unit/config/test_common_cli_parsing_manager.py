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

from powerapi.config.cli_parser import CLIParseException
from powerapi.config.common_cli_parsing_manager import (
    CommonCLIParsingManager,
    PreProcessorSchema,
    PullerSchema,
    PusherSchema,
    generate_env_prefix,
)
from powerapi.exception import ConfigurationError


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


def test_puller_config_schema_registers_default_model_argument():
    """
    Test that PullerSchema registers the default report model argument.
    """
    schema = PullerSchema('pytest')
    model_argument = schema.arguments['model']

    assert model_argument.name == 'model'
    assert model_argument.default_value == 'HWPCReport'


def test_pusher_config_schema_registers_default_model_argument():
    """
    Test that PusherSchema registers the default report model argument.
    """
    schema = PusherSchema('pytest')
    model_argument = schema.arguments['model']

    assert model_argument.name == 'model'
    assert model_argument.default_value == 'PowerReport'


def test_pre_processor_config_schema_registers_mandatory_puller_argument():
    """
    Test that PreProcessorSchema registers a mandatory puller argument.
    """
    schema = PreProcessorSchema('pytest')
    puller_argument = schema.arguments['puller']

    assert puller_argument.name == 'puller'
    assert puller_argument.is_mandatory is True


def test_common_cli_manager_registers_root_environment_prefix():
    """
    Test that CommonCLIParsingManager registers the root PowerAPI environment prefix.
    """
    manager = CommonCLIParsingManager()

    assert manager.schema.arguments_prefix == ['POWERAPI_']


def test_common_cli_manager_registers_group_environment_prefixes():
    """
    Test that CommonCLIParsingManager registers every group environment prefix.
    """
    manager = CommonCLIParsingManager()

    assert {name: group.prefix for name, group in manager.schema.groups.items() if group.prefix} == {
        'input': 'POWERAPI_INPUT_',
        'output': 'POWERAPI_OUTPUT_',
        'pre-processor': 'POWERAPI_PRE_PROCESSOR_',
        'post-processor': 'POWERAPI_POST_PROCESSOR_',
    }


def test_common_cli_manager_registers_top_level_groups():
    """
    Test that CommonCLIParsingManager registers every top-level group.
    """
    manager = CommonCLIParsingManager()

    assert set(manager.schema.groups) == {
        'input',
        'output',
        'pre-processor',
        'post-processor',
    }


def test_common_cli_manager_registers_input_schemas():
    """
    Test that CommonCLIParsingManager registers every built-in input schema.
    """
    manager = CommonCLIParsingManager()

    assert set(manager.schema.groups['input'].components) == {
        'mongodb',
        'socket',
        'csv',
        'json',
    }


def test_common_cli_manager_registers_output_schemas():
    """
    Test that CommonCLIParsingManager registers every built-in output schema.
    """
    manager = CommonCLIParsingManager()

    assert set(manager.schema.groups['output'].components) == {
        'mongodb',
        'prometheus',
        'csv',
        'json',
        'influxdb2',
        'clickhouse',
    }


def test_common_cli_manager_registers_pre_processor_schemas():
    """
    Test that CommonCLIParsingManager registers every built-in pre-processor schema.
    """
    manager = CommonCLIParsingManager()

    assert set(manager.schema.groups['pre-processor'].components) == {
        'kubernetes',
        'openstack',
    }


def test_common_cli_manager_registers_verbose_argument():
    """
    Test that CommonCLIParsingManager registers the verbose root argument.
    """
    manager = CommonCLIParsingManager()
    verbose_argument = manager.schema.arguments['verbose']

    assert verbose_argument.name == 'verbose'
    assert verbose_argument.is_flag is True
    assert verbose_argument.default_value is False


def test_common_cli_manager_registers_stream_argument():
    """
    Test that CommonCLIParsingManager registers the stream root argument.
    """
    manager = CommonCLIParsingManager()
    stream_argument = manager.schema.arguments['stream']

    assert stream_argument.name == 'stream'
    assert stream_argument.is_flag is True
    assert stream_argument.default_value is False


def test_common_cli_manager_validates_output_config_without_name():
    """
    Test that output config validation can use the output key as the pusher name.
    """
    manager = CommonCLIParsingManager()
    config = {
        'output': {
            'powerrep': {
                'model': 'PowerReport',
                'type': 'json',
                'filepath': '/tmp/powerapi-output.jsonl',
            },
        },
    }

    result = manager.validate(config)

    assert result['output']['powerrep']['type'] == 'json'
    assert result['output']['powerrep']['model'] == 'PowerReport'
    assert result['output']['powerrep']['filepath'] == '/tmp/powerapi-output.jsonl'
    assert result['output']['powerrep']['compression'] == 'auto'


def test_common_cli_manager_rejects_legacy_contextual_configuration():
    """
    Test that the breaking CLI no longer accepts contextual component arguments.
    """
    manager = CommonCLIParsingManager()

    with pytest.raises(CLIParseException) as result:
        manager.parse([
            '--output', 'json',
            '--filepath', '/tmp/powerapi-output.jsonl',
        ])

    assert 'unrecognized arguments' in result.value.msg


def test_common_cli_manager_parse_cli_configuration():
    """
    Test that CommonCLIParsingManager parses a representative CLI configuration.
    """
    manager = CommonCLIParsingManager()

    result = manager.parse([
        '--verbose',
        '-C', 'input.pytest-puller.type=csv',
        '-C', 'input.pytest-puller.files=a.csv,b.csv',
        '-C', 'output.pytest-pusher.type=json',
        '-C', 'output.pytest-pusher.filepath=/tmp/pytest-powerapi.jsonl',
    ])

    assert result['verbose'] is True
    assert result['input']['pytest-puller']['type'] == 'csv'
    assert result['input']['pytest-puller']['files'] == ['a.csv', 'b.csv']
    assert result['output']['pytest-pusher']['type'] == 'json'
    assert result['output']['pytest-pusher']['filepath'] == '/tmp/pytest-powerapi.jsonl'


def test_common_cli_manager_resolves_component_type_after_merging_environment(monkeypatch):
    """
    Test that a partial CLI override inherits its component type from the environment.
    """
    monkeypatch.setenv('POWERAPI_INPUT_sensor_TYPE', 'socket')
    manager = CommonCLIParsingManager()

    result = manager.parse([
        'powerapi',
        '-C', 'input.sensor.port=9090',
    ])

    assert result['input']['sensor'] == {
        'type': 'socket',
        'model': 'HWPCReport',
        'host': 'localhost',
        'port': 9090,
    }


def test_common_cli_manager_rejects_unknown_dotted_component_property():
    """
    Test that an unknown dotted component property is rejected with its full path.
    """
    manager = CommonCLIParsingManager()

    with pytest.raises(ConfigurationError) as result:
        manager.parse([
            'powerapi',
            '-C', 'input.sensor.type=socket',
            '-C', 'input.sensor.unknown=value',
        ])

    assert result.value.path == 'input.sensor.unknown'


@pytest.mark.parametrize(('property_name', 'value'), [
    ('p', 9090),
    ('name', 'legacy-name'),
])
def test_common_cli_manager_rejects_legacy_component_properties(property_name, value):
    """
    Test that removed shortened component property names are rejected.
    """
    manager = CommonCLIParsingManager()
    config = {'input': {'sensor': {'type': 'socket', property_name: value}}}

    with pytest.raises(ConfigurationError) as result:
        manager.validate(config)

    assert result.value.path == f'input.sensor.{property_name}'


def test_common_cli_manager_requires_component_type_after_merging():
    """
    Test that a component type is required after all configuration sources are merged.
    """
    manager = CommonCLIParsingManager()

    with pytest.raises(ConfigurationError) as result:
        manager.parse([
            'powerapi',
            '-C', 'input.sensor.port=9090',
        ])

    assert result.value.path == 'input.sensor.type'
