# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

import json
import sys

import pytest

from powerapi.config.cli_parser import CLIParseException
from powerapi.config.config_parser import ComponentSchema, ConfigurationSectionSchema
from powerapi.config.parsing_manager import ConfigurationParsingManager
from powerapi.exception import ConfigurationError


@pytest.fixture
def parsing_manager() -> ConfigurationParsingManager:
    """
    Create a parsing manager with representative root and component configuration.
    :return: Configured parsing manager.
    """
    manager = ConfigurationParsingManager()
    manager.add_argument_prefix('TEST_POWERAPI_')
    manager.add_argument('verbose', is_flag=True, default_value=False)
    manager.add_argument('interval', argument_type=int, default_value=10)
    manager.add_group('input', prefix='TEST_POWERAPI_INPUT_')

    socket = ComponentSchema('socket')
    socket.add_argument('host', default_value='localhost')
    socket.add_argument('port', argument_type=int, default_value=9080)
    socket.add_argument('tags', argument_type=list)
    manager.add_component('input', socket)

    return manager


def test_parse_merges_cli_assignments_and_validates_schema(parsing_manager):
    """
    Test that CLI values are merged, cast, and completed with schema defaults.
    """
    result = parsing_manager.parse([
        'powerapi',
        '--verbose',
        '-C', 'input.sensor.type=socket',
        '-C', 'input.sensor.port=9090',
        '-C', 'input.sensor.tags=host,pod',
    ])

    assert result == {
        'verbose': True,
        'interval': 10,
        'input': {
            'sensor': {
                'type': 'socket',
                'host': 'localhost',
                'port': 9090,
                'tags': ['host', 'pod'],
            },
        },
    }


def test_parse_validates_fixed_section_without_component_type():
    """
    Test that CLI assignments configure a fixed group section without a type.
    """
    manager = ConfigurationParsingManager()
    manager.add_group('formula')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int)
    manager.add_section('formula', 'smartwatts', smartwatts)

    result = manager.parse([
        'powerapi',
        '-C', 'formula.smartwatts.learn-error-window-size=10',
    ])

    assert result == {
        'formula': {
            'smartwatts': {
                'learn-error-window-size': 10,
            },
        },
    }


@pytest.mark.parametrize('args', [
    ['powerapi', '--interval', '12'],
    ['--interval', '12'],
])
def test_parse_accepts_arguments_with_or_without_executable(parsing_manager, args):
    """
    Test that parsing accepts argument lists with or without an executable name.
    """
    assert parsing_manager.parse(args) == {'verbose': False, 'interval': 12}


def test_parse_uses_sys_argv_by_default(parsing_manager, monkeypatch):
    """
    Test that parsing uses the process arguments when no argument list is provided.
    """
    monkeypatch.setattr(sys, 'argv', ['powerapi', '--interval', '12'])

    assert parsing_manager.parse() == {'verbose': False, 'interval': 12}


def test_parse_applies_defaults_when_sources_are_empty(parsing_manager):
    """
    Test that parsing an empty configuration applies root defaults.
    """
    assert parsing_manager.parse([]) == {'verbose': False, 'interval': 10}


def test_parse_merges_sources_with_cli_then_environment_then_file_precedence(parsing_manager, monkeypatch, tmp_path):
    """
    Test CLI, environment, and file precedence for root and component values.
    """
    config_file = tmp_path / 'powerapi-pytest.json'
    config_file.write_text(json.dumps({
        'interval': 1,
        'input': {
            'sensor': {
                'type': 'socket',
                'host': 'file',
                'port': 1001,
                'tags': ['file'],
            },
        },
    }), encoding='utf-8')
    monkeypatch.setenv('TEST_POWERAPI_INTERVAL', '2')
    monkeypatch.setenv('TEST_POWERAPI_INPUT_SENSOR_HOST', 'environment')
    monkeypatch.setenv('TEST_POWERAPI_INPUT_SENSOR_PORT', '2002')

    result = parsing_manager.parse([
        'powerapi',
        '--config-file', str(config_file),
        '-C', 'interval=3',
        '-C', 'input.sensor.port=3003',
    ])

    assert result == {
        'verbose': False,
        'interval': 3,
        'input': {
            'sensor': {
                'type': 'socket',
                'host': 'environment',
                'port': 3003,
                'tags': ['file'],
            },
        },
    }


def test_parse_resolves_environment_component_type_for_partial_file_configuration(parsing_manager, monkeypatch, tmp_path):
    """
    Test that a partial file component inherits its type from the environment after merging.
    """
    config_file = tmp_path / 'powerapi-pytest.json'
    config_file.write_text(json.dumps({
        'input': {
            'sensor': {
                'port': 9080,
            },
        },
    }), encoding='utf-8')
    monkeypatch.setenv('TEST_POWERAPI_INPUT_SENSOR_TYPE', 'socket')

    result = parsing_manager.parse([
        'powerapi',
        '--config-file', str(config_file),
    ])

    assert result['input']['sensor'] == {
        'type': 'socket',
        'host': 'localhost',
        'port': 9080,
    }


def test_parse_propagates_cli_errors(parsing_manager):
    """
    Test that command-line parsing errors propagate to the caller.
    """
    with pytest.raises(CLIParseException, match='unrecognized arguments'):
        parsing_manager.parse(['powerapi', '--unknown'])


def test_parse_propagates_configuration_errors(parsing_manager):
    """
    Test that schema validation errors propagate with their configuration path.
    """
    with pytest.raises(ConfigurationError) as result:
        parsing_manager.parse(['powerapi', '-C', 'input.sensor.type=unknown'])

    assert result.value.path == 'input.sensor.type'


def test_parse_propagates_missing_configuration_file(parsing_manager, tmp_path):
    """
    Test that selecting a missing configuration file raises FileNotFoundError.
    """
    missing_file = tmp_path / 'powerapi-pytest-missing.json'

    with pytest.raises(FileNotFoundError):
        parsing_manager.parse(['powerapi', '--config-file', str(missing_file)])
