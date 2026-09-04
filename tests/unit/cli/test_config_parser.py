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

import json

import pytest

from powerapi.cli.config_loader import EnvironmentConfigLoader, JSONConfigLoader
from powerapi.cli.config_parser import (
    ComponentSchema,
    ConfigurationSchema,
    ConfigurationSectionSchema,
)
from powerapi.exception import ConfigurationError


def test_schema_registers_argument_definition():
    """
    Test that a configuration property is registered with its definition.
    """
    schema = ConfigurationSectionSchema()

    schema.add_argument('port', argument_type=int, default_value=9080)

    definition = schema.arguments['port']
    assert definition.name == 'port'
    assert definition.argument_type is int
    assert definition.default_value == 9080


def test_schema_rejects_duplicate_property():
    """
    Test that a configuration property cannot be registered more than once.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('port')

    with pytest.raises(ValueError, match='already registered'):
        schema.add_argument('port')

def test_schema_casts_and_applies_defaults():
    """
    Test that schema validation casts canonical property values and applies defaults.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('port', argument_type=int)
    schema.add_argument('enabled', argument_type=bool, default_value=False)
    schema.add_argument('tags', argument_type=list)

    result = schema.validate({'port': '9080', 'tags': 'host,socket'})

    assert result == {
        'port': 9080,
        'enabled': False,
        'tags': ['host', 'socket'],
    }


def test_schema_copies_mutable_defaults():
    """
    Test that mutating a validated default does not modify later configurations.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('tags', argument_type=list, default_value=[])

    first_result = schema.validate({})
    first_result['tags'].append('sensor')

    assert schema.validate({}) == {'tags': []}


def test_schema_rejects_invalid_boolean_value():
    """
    Test that an unrecognized textual boolean value is rejected.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('enabled', argument_type=bool)

    with pytest.raises(ConfigurationError) as result:
        schema.validate({'enabled': 'invalid'})

    assert result.value.path == 'enabled'
    assert result.value.reason == 'Expected bool'


def test_schema_rejects_missing_mandatory_property():
    """
    Test that a missing mandatory property is reported with its path.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('uri', is_mandatory=True)

    with pytest.raises(ConfigurationError) as result:
        schema.validate({})

    assert result.value.path == 'uri'
    assert result.value.reason == 'Missing required value'


@pytest.mark.parametrize(('argument_type', 'value', 'expected'), [
    (str, '', ''),
    (list, '', []),
])
def test_schema_accepts_empty_mandatory_property(argument_type, value, expected):
    """
    Test that mandatory properties require presence but may contain empty values.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('value', argument_type=argument_type, is_mandatory=True)

    assert schema.validate({'value': value}) == {'value': expected}


def test_schema_rejects_unknown_property():
    """
    Test that an unknown property is reported with its path.
    """
    with pytest.raises(ConfigurationError) as result:
        ConfigurationSectionSchema().validate({'unknown': 'value'})

    assert result.value.path == 'unknown'
    assert result.value.reason == 'Unknown property'


def test_schema_rejects_cli_alias_as_configuration_property():
    """
    Test that schema validation only accepts canonical configuration property names.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('port', argument_type=int)

    with pytest.raises(ConfigurationError) as result:
        schema.validate({'p': '9080'})

    assert result.value.path == 'p'
    assert result.value.reason == 'Unknown property'


def test_schema_reports_bad_type():
    """
    Test that an invalid property value reports the expected type and path.
    """
    schema = ConfigurationSectionSchema()
    schema.add_argument('port', argument_type=int)

    with pytest.raises(ConfigurationError) as result:
        schema.validate({'port': 'not-an-integer'})

    assert result.value.path == 'port'
    assert result.value.reason == 'Expected int'


def test_root_schema_validates_component_without_synthetic_name_property():
    """
    Test that component names come from group keys rather than synthetic properties.
    """
    schema = ConfigurationSchema()
    schema.add_group('input', prefix='POWERAPI_INPUT_')
    component = ComponentSchema('socket')
    component.add_argument('port', argument_type=int, default_value=9080)
    schema.add_component('input', component)

    result = schema.validate({'input': {'sensor': {'type': 'socket'}}})

    assert result == {'input': {'sensor': {'type': 'socket', 'port': 9080}}}


def test_root_schema_prefixes_component_validation_error():
    """
    Test that component validation errors contain the complete dotted path.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')
    component = ComponentSchema('socket')
    component.add_argument('port', argument_type=int)
    schema.add_component('input', component)

    with pytest.raises(ConfigurationError) as result:
        schema.validate({'input': {'sensor': {'type': 'socket', 'port': 'invalid'}}})

    assert result.value.path == 'input.sensor.port'
    assert result.value.reason == 'Expected int'
    assert result.value.msg == 'Invalid configuration at "input.sensor.port": Expected int'


@pytest.mark.parametrize('configuration', [
    {'input': {'sensor': {}}},
    {'input': {'sensor': {'type': 'unknown'}}},
    {'input': {'sensor': {'type': {}}}},
])
def test_root_schema_requires_known_component_type(configuration):
    """
    Test that components require a registered component type.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')

    with pytest.raises(ConfigurationError) as result:
        schema.validate(configuration)

    assert result.value.path == 'input.sensor.type'


def test_root_schema_validates_fixed_section_without_component_type():
    """
    Test that a fixed group section is validated without a component type.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int)
    schema.add_section('formula', 'smartwatts', smartwatts)

    result = schema.validate({
        'formula': {
            'smartwatts': {
                'learn-error-window-size': '10',
            },
        },
    })

    assert result == {
        'formula': {
            'smartwatts': {
                'learn-error-window-size': 10,
            },
        },
    }


def test_root_schema_applies_defaults_from_fixed_section():
    """
    Test that fixed section defaults are applied when the section is omitted.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int, default_value=10)
    schema.add_section('formula', 'smartwatts', smartwatts)

    result = schema.validate({})

    assert result == {
        'formula': {
            'smartwatts': {
                'learn-error-window-size': 10,
            },
        },
    }


def test_root_schema_rejects_component_type_in_fixed_section():
    """
    Test that a fixed group section does not accept a component type selector.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula')
    schema.add_section('formula', 'smartwatts', ConfigurationSectionSchema())

    with pytest.raises(ConfigurationError) as result:
        schema.validate({'formula': {'smartwatts': {'type': 'smartwatts'}}})

    assert result.value.path == 'formula.smartwatts.type'
    assert result.value.reason == 'Unknown property'


def test_root_schema_rejects_unregistered_type_property():
    """
    Test that the component type selector is not accepted as a root property.
    """
    with pytest.raises(ConfigurationError) as result:
        ConfigurationSchema().validate({'type': 'socket'})

    assert result.value.path == 'type'
    assert result.value.reason == 'Unknown property'


@pytest.mark.parametrize(('configuration', 'path'), [
    ({'input': []}, 'input'),
    ({'input': {'sensor': []}}, 'input.sensor'),
])
def test_root_schema_rejects_non_dictionary_group_values(configuration, path):
    """
    Test that configuration groups and their entries must be dictionaries.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')

    with pytest.raises(ConfigurationError) as result:
        schema.validate(configuration)

    assert result.value.path == path
    assert result.value.reason == 'Expected dict'


def test_json_loader_rejects_shortened_property_names(tmp_path):
    """
    Test that JSON loading only accepts registered configuration property names.
    """
    schema = ConfigurationSchema()
    schema.add_argument('port', argument_type=int, default_value=9080)
    config_file = tmp_path / 'powerapi-pytest.json'
    config_file.write_text(json.dumps({'p': '9090'}), encoding='utf-8')

    configuration = JSONConfigLoader().load(str(config_file))
    with pytest.raises(ConfigurationError) as result:
        schema.validate(configuration)

    assert result.value.path == 'p'
    assert result.value.reason == 'Unknown property'


def test_json_loader_loads_fixed_section_without_component_type(tmp_path):
    """
    Test that JSON loading preserves a fixed group section without a type.
    """
    config_file = tmp_path / 'powerapi-pytest.json'
    config_file.write_text(json.dumps({
        'formula': {
            'smartwatts': {
                'learn-error-window-size': 10,
            },
        },
    }), encoding='utf-8')

    result = JSONConfigLoader().load(str(config_file))

    assert result == {
        'formula': {
            'smartwatts': {
                'learn-error-window-size': 10,
            },
        },
    }


def test_json_loader_returns_empty_configuration_without_file():
    """
    Test that JSON loading returns an empty configuration when no file is selected.
    """
    assert JSONConfigLoader().load(None) == {}


def test_json_loader_reports_invalid_json_as_configuration_error(tmp_path):
    """
    Test that invalid JSON is exposed as a ConfigurationError with decoder details.
    """
    config_file = tmp_path / 'powerapi-pytest.json'
    invalid_json = '{"stream": true,}'
    config_file.write_text(invalid_json, encoding='utf-8')

    with pytest.raises(json.JSONDecodeError) as decode_error:
        json.loads(invalid_json)

    with pytest.raises(ConfigurationError) as result:
        JSONConfigLoader().load(str(config_file))

    assert result.value.path is None
    assert result.value.reason == f'Invalid JSON in configuration file "{config_file}": {decode_error.value}'


@pytest.mark.parametrize('content', ['[]', 'null', '"value"'])
def test_json_loader_rejects_non_object_root(content, tmp_path):
    """
    Test that a JSON configuration must contain an object at its root.
    """
    config_file = tmp_path / 'powerapi-pytest.json'
    config_file.write_text(content, encoding='utf-8')

    with pytest.raises(ConfigurationError) as result:
        JSONConfigLoader().load(str(config_file))

    assert result.value.reason == 'Expected a JSON object'


def test_environment_loader_preserves_root_and_component_format(monkeypatch):
    """
    Test that environment loading preserves raw root and nested component values.
    """
    schema = ConfigurationSchema()
    schema.add_argument_prefix('POWERAPI_')
    schema.add_argument('stream', argument_type=bool)
    schema.add_group('input', prefix='POWERAPI_INPUT_')
    component = ComponentSchema('socket')
    component.add_argument('port', argument_type=int)
    schema.add_component('input', component)
    monkeypatch.setenv('POWERAPI_STREAM', 'true')
    monkeypatch.setenv('POWERAPI_INPUT_SENSOR_TYPE', 'socket')
    monkeypatch.setenv('POWERAPI_INPUT_SENSOR_PORT', '9080')

    result = EnvironmentConfigLoader(schema).load()

    assert result == {
        'stream': 'true',
        'input': {'sensor': {'type': 'socket', 'port': '9080'}},
    }


def test_environment_loader_ignores_group_without_prefix(monkeypatch):
    """
    Test that a prefixless group does not hide root values or inspect unrelated environment variables.
    """
    schema = ConfigurationSchema()
    schema.add_argument_prefix('POWERAPI_')
    schema.add_argument('stream', argument_type=bool)
    schema.add_group('formula')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int)
    schema.add_section('formula', 'smartwatts', smartwatts)
    monkeypatch.setenv('POWERAPI_STREAM', 'true')
    monkeypatch.setenv('SMARTWATTS_LEARN_ERROR_WINDOW_SIZE', '10')

    result = EnvironmentConfigLoader(schema).load()

    assert result == {'stream': 'true'}


def test_environment_loader_preserves_fixed_section_without_component_type(monkeypatch):
    """
    Test that environment loading preserves a raw fixed group section.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula', prefix='POWERAPI_FORMULA_')
    smartwatts = ConfigurationSectionSchema()
    smartwatts.add_argument('learn-error-window-size', argument_type=int)
    schema.add_section('formula', 'smartwatts', smartwatts)
    monkeypatch.setenv('POWERAPI_FORMULA_SMARTWATTS_LEARN_ERROR_WINDOW_SIZE', '10')

    result = EnvironmentConfigLoader(schema).load()

    assert result == {
        'formula': {
            'smartwatts': {
                'learn-error-window-size': '10',
            },
        },
    }


def test_environment_loader_rejects_component_type_in_fixed_section(monkeypatch):
    """
    Test that an environment fixed section does not accept a component type selector.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula', prefix='POWERAPI_FORMULA_')
    schema.add_section('formula', 'smartwatts', ConfigurationSectionSchema())
    monkeypatch.setenv('POWERAPI_FORMULA_SMARTWATTS_TYPE', 'smartwatts')

    configuration = EnvironmentConfigLoader(schema).load()
    with pytest.raises(ConfigurationError) as result:
        schema.validate(configuration)

    assert result.value.path == 'formula.smartwatts.type'
    assert result.value.reason == 'Unknown property'


def test_environment_loader_preserves_component_without_type(monkeypatch):
    """
    Test that environment loading preserves a partial component for later merging.
    """
    schema = ConfigurationSchema()
    schema.add_group('input', prefix='POWERAPI_INPUT_')
    component = ComponentSchema('socket')
    component.add_argument('port', argument_type=int)
    schema.add_component('input', component)
    monkeypatch.setenv('POWERAPI_INPUT_SENSOR_PORT', '9080')

    assert EnvironmentConfigLoader(schema).load() == {
        'input': {'sensor': {'port': '9080'}},
    }


def test_root_schema_rejects_overlapping_environment_prefixes():
    """
    Test that overlapping root environment prefixes are rejected.
    """
    schema = ConfigurationSchema()
    schema.add_argument_prefix('POWERAPI_')

    with pytest.raises(ValueError, match='conflicts with'):
        schema.add_argument_prefix('POWERAPI_INPUT_')


def test_root_schema_rejects_duplicate_group():
    """
    Test that a configuration group cannot be registered more than once.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')

    with pytest.raises(ValueError, match='already registered'):
        schema.add_group('input')


def test_root_schema_rejects_group_matching_property():
    """
    Test that a group cannot reuse a registered root property name.
    """
    schema = ConfigurationSchema()
    schema.add_argument('input')

    with pytest.raises(ValueError, match='already registered as a property'):
        schema.add_group('input')


def test_root_schema_rejects_property_matching_group():
    """
    Test that a root property cannot reuse a registered group name.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')

    with pytest.raises(ValueError, match='already registered as a group'):
        schema.add_argument('input')


def test_root_schema_rejects_duplicate_component_type():
    """
    Test that a component type cannot be registered twice in one group.
    """
    schema = ConfigurationSchema()
    schema.add_group('input')
    schema.add_component('input', ComponentSchema('socket'))

    with pytest.raises(ValueError, match='already registered'):
        schema.add_component('input', ComponentSchema('socket'))


def test_root_schema_rejects_component_for_unknown_group():
    """
    Test that a component cannot be registered in an unknown group.
    """
    schema = ConfigurationSchema()

    with pytest.raises(ValueError, match='is not registered'):
        schema.add_component('input', ComponentSchema('socket'))


def test_root_schema_rejects_section_for_unknown_group():
    """
    Test that a fixed section cannot be registered in an unknown group.
    """
    schema = ConfigurationSchema()

    with pytest.raises(ValueError, match='is not registered'):
        schema.add_section('formula', 'smartwatts', ConfigurationSectionSchema())


def test_root_schema_rejects_duplicate_section():
    """
    Test that a fixed section name cannot be registered twice in one group.
    """
    schema = ConfigurationSchema()
    schema.add_group('formula')
    schema.add_section('formula', 'smartwatts', ConfigurationSectionSchema())

    with pytest.raises(ValueError, match='already registered'):
        schema.add_section('formula', 'smartwatts', ConfigurationSectionSchema())
