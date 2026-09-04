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

import argparse

import pytest

from powerapi.config import cli_parser
from powerapi.config.cli_parser import CLIArgumentParser, CLIParseException
from powerapi.config.config_parser import (
    ComponentSchema,
    ConfigurationSchema,
    ConfigurationSectionSchema,
)


def create_parser() -> CLIArgumentParser:
    """
    Create a CLI parser backed by an empty configuration schema.
    :return: CLI parser accepting only built-in options.
    """
    return CLIArgumentParser(ConfigurationSchema())


def test_configuration_help_uses_plain_theme_without_argparse_theme(monkeypatch):
    """
    Test that configuration help falls back to plain text when argparse has no theme.
    """
    monkeypatch.setattr(cli_parser.argparse, 'RawDescriptionHelpFormatter', lambda _: object())

    assert cli_parser._get_argparse_theme() == cli_parser._HelpTheme()


def test_cli_argument_parser_preserves_equals_in_assignment_value():
    """
    Test that assignment values preserve equals signs after the first separator.
    """
    result = create_parser().parse([
        '-C', 'input.mongo.uri=mongodb://localhost/?option=value',
    ])

    assert result.configuration == {
        'input': {'mongo': {'uri': 'mongodb://localhost/?option=value'}},
    }


@pytest.mark.parametrize('expression', [
    'input.mongo.uri',
    '=value',
    'input..uri=value',
    '.input=value',
    'input.sensor=value',
    'input.sensor.connection.uri=value',
])
def test_cli_argument_parser_rejects_invalid_assignment(expression):
    """
    Test that malformed or unsupported assignment paths are rejected.
    """
    with pytest.raises(CLIParseException):
        create_parser().parse(['-C', expression])


def test_cli_argument_parser_builds_nested_configuration():
    """
    Test that root and component assignments build a nested configuration.
    """
    result = create_parser().parse([
        '-C', 'input.sensor.type=socket',
        '-C', 'input.sensor.port=9080',
        '-C', 'stream=false',
    ])

    assert result.configuration == {
        'input': {
            'sensor': {
                'type': 'socket',
                'port': '9080',
            },
        },
        'stream': 'false',
    }


def test_cli_argument_parser_uses_last_repeated_value():
    """
    Test that the last assignment to a path replaces previous values.
    """
    result = create_parser().parse([
        '-C', 'input.sensor.port=9080',
        '-C', 'input.sensor.port=9090',
    ])

    assert result.configuration['input']['sensor']['port'] == '9090'


@pytest.mark.parametrize('expressions', [
    ['input=value', 'input.sensor.port=9090'],
    ['input.sensor.port=9090', 'input=value'],
])
def test_cli_argument_parser_rejects_structural_conflict(expressions):
    """
    Test that scalar and nested assignments cannot target the same path.
    """
    arguments = [argument for expression in expressions for argument in ('-C', expression)]

    with pytest.raises(CLIParseException):
        create_parser().parse(arguments)


def test_cli_argument_parser_parses_repeatable_config_assignments():
    """
    Test repeatable assignment options and configuration-file selection.
    """
    parser = create_parser()

    result = parser.parse([
        '-C', 'input.sensor.type=socket',
        '--set-config', 'input.sensor.port=9080',
        '--config-file', '/tmp/powerapi.json',
    ])

    assert result.config_file == '/tmp/powerapi.json'
    assert result.configuration == {
        'input': {
            'sensor': {
                'type': 'socket',
                'port': '9080',
            },
        },
    }


def test_cli_argument_parser_keeps_internal_values_separate_from_root_arguments():
    """
    Test that internal parser destinations do not collide with schema properties.
    """
    schema = ConfigurationSchema()
    schema.add_argument('config_assignments')
    schema.add_argument('config_file')
    parser = CLIArgumentParser(schema)

    result = parser.parse([
        '--config_assignments', 'root-value',
        '--config_file', 'another-root-value',
        '-C', 'stream=false',
        '--config-file', '/tmp/powerapi.json',
    ])

    assert result.config_file == '/tmp/powerapi.json'
    assert result.configuration == {
        'config_assignments': 'root-value',
        'config_file': 'another-root-value',
        'stream': 'false',
    }


def test_cli_argument_parser_reports_argument_conflict_as_cli_error():
    """
    Test that schema option conflicts are reported as CLIParseException.
    """
    schema = ConfigurationSchema()
    schema.add_argument('config-file')
    parser = CLIArgumentParser(schema)

    with pytest.raises(CLIParseException) as result:
        parser.parse([])

    assert result.value.msg == 'Failed to add argument: argument --config-file: conflicting option string: --config-file'
    assert isinstance(result.value.__cause__, argparse.ArgumentError)


def test_cli_argument_parser_does_not_add_absent_root_argument():
    """
    Test that omitted root options are absent from the raw CLI configuration.
    """
    schema = ConfigurationSchema()
    schema.add_argument('stream', is_flag=True)
    parser = CLIArgumentParser(schema)

    result = parser.parse([])

    assert 'stream' not in result.configuration


def test_cli_argument_parser_parses_registered_root_flag():
    """
    Test that a registered root flag produces its configuration property.
    """
    schema = ConfigurationSchema()
    schema.add_argument('stream', is_flag=True)
    parser = CLIArgumentParser(schema)

    result = parser.parse(['--stream'])

    assert result.configuration == {'stream': True}


def test_cli_argument_parser_keeps_non_flag_root_value_raw():
    """
    Test that non-flag root values remain raw until schema validation.
    """
    schema = ConfigurationSchema()
    schema.add_argument('port')
    parser = CLIArgumentParser(schema)

    result = parser.parse(['--port', '9080'])

    assert result.configuration == {'port': '9080'}


def test_cli_argument_parser_preserves_root_argument_underscores():
    """
    Test that underscores in root option names are preserved.
    """
    schema = ConfigurationSchema()
    schema.add_argument('some_value')
    parser = CLIArgumentParser(schema)

    result = parser.parse(['--some_value', 'test'])

    assert result.configuration == {'some_value': 'test'}


def test_cli_argument_parser_rejects_contextual_argument():
    """
    Test that legacy contextual component options are rejected.
    """
    parser = create_parser()

    with pytest.raises(CLIParseException) as result:
        parser.parse(['--input', 'socket'])

    assert result.value.msg == 'Failed to parse CLI: unrecognized arguments: --input socket'
    assert isinstance(result.value.__cause__, argparse.ArgumentError)


def test_cli_argument_parser_prints_help(capsys):
    """
    Test that --help prints usage information and exits successfully.
    """
    parser = create_parser()

    with pytest.raises(SystemExit) as result:
        parser.parse(['--help'])

    help_message = capsys.readouterr().out

    assert result.value.code == 0
    assert help_message.startswith('usage:')
    assert '-C PATH=VALUE' in help_message
    assert '--config-file FILE' in help_message


def test_cli_argument_parser_help_contains_schema_paths(capsys):
    """
    Test that help exposes canonical schema paths and supported component types.
    """
    schema = ConfigurationSchema()
    schema.add_argument('verbose', is_flag=True)
    schema.add_group('input')
    component = ComponentSchema('socket')
    component.add_argument('port', argument_type=int)
    schema.add_component('input', component)
    schema.add_group('formula')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int)
    schema.add_section('formula', 'smartwatts', smartwatts)

    with pytest.raises(SystemExit):
        CLIArgumentParser(schema).parse(['--help'])

    help_lines = {
        line.strip()
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    }
    expected_lines = {
        'verbose',
        'input.NAME.type',
        'Supported types: socket',
        'input.NAME.type=socket',
        'input.NAME.port',
        'formula.smartwatts.learn-error-window-size',
    }
    excluded_lines = {
        'v',
        'input.NAME.p',
        'formula.smartwatts.w',
        'formula.smartwatts.type',
    }

    assert expected_lines.issubset(help_lines)
    assert excluded_lines.isdisjoint(help_lines)
