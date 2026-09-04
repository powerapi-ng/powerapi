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

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from powerapi.exception import ConfigurationError

from ._utils import string_to_bool, string_to_list


@dataclass(frozen=True)
class ArgumentDefinition:
    """
    Definition of a configuration property.
    """
    name: str
    is_flag: bool = False
    default_value: Any = None
    help_text: str = ''
    argument_type: type[Any] = str
    is_mandatory: bool = False


class ConfigurationSectionSchema:
    """
    Schema for a flat set of configuration properties.
    """

    def __init__(self) -> None:
        self.arguments: dict[str, ArgumentDefinition] = {}

    def add_argument(
        self,
        name: str,
        *,
        is_flag: bool = False,
        default_value: Any = None,
        help_text: str = '',
        argument_type: type = str,
        is_mandatory: bool = False,
    ) -> None:
        """
        Register a configuration property.
        :param name: Configuration property name.
        :param is_flag: Whether the property represents a boolean flag.
        :param default_value: Value used when the property is omitted.
        :param help_text: User-facing description of the property.
        :param argument_type: Type used to cast non-flag values.
        :param is_mandatory: Whether the property must be defined.
        :raises ValueError: If the property name is already registered.
        """
        if name in self.arguments:
            raise ValueError(f'Configuration property "{name}" is already registered')

        self.arguments[name] = ArgumentDefinition(
            name=name,
            is_flag=is_flag,
            default_value=default_value,
            help_text=help_text,
            argument_type=bool if is_flag else argument_type,
            is_mandatory=is_mandatory,
        )

    def validate(self, conf: dict, path: str = '') -> dict:
        """
        Cast properties, require mandatory values, and apply defaults.
        :param conf: Partial configuration to validate.
        :param path: Dotted path prepended to configuration errors.
        :return: Validated configuration with defaults applied.
        :raises ConfigurationError: If the configuration is not a dictionary or contains an unknown, missing, or incorrectly typed property.
        """
        if not isinstance(conf, dict):
            raise ConfigurationError('Expected dict', path or None)

        validated = {}
        for name, value in conf.items():
            if name not in self.arguments:
                raise ConfigurationError('Unknown property', _join_path(path, name))

            validated[name] = cast_argument_value(_join_path(path, name), value, self.arguments[name])

        definitions = self.arguments.values()
        for argument in definitions:
            name = argument.name
            if name not in validated:
                if argument.is_mandatory:
                    raise ConfigurationError('Missing required value', _join_path(path, name))
                if argument.default_value is not None:
                    validated[name] = deepcopy(argument.default_value)

        return validated


class ComponentSchema(ConfigurationSectionSchema):
    """
    Schema for one component type in a configuration group.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a component schema.
        :param name: Component type handled by this schema.
        """
        super().__init__()
        self.name = name


class ComponentGroupSchema:
    """
    Schemas for the dynamic components and fixed sections in a configuration group.
    """

    def __init__(self, group_name: str, help_text: str = '', prefix: str = '') -> None:
        """
        Initialize a configuration group schema.
        :param group_name: Configuration name of the group.
        :param help_text: User-facing description of the group.
        :param prefix: Environment-variable prefix assigned to the group.
        """
        self.group_name = group_name
        self.help_text = help_text
        self.prefix = prefix
        self.components: dict[str, ComponentSchema] = {}
        self.sections: dict[str, ConfigurationSectionSchema] = {}

    def get_argument_names(self) -> list[str]:
        """
        Return all canonical property names accepted by the group.
        :return: Canonical component and section property names without duplicates.
        """
        names = []
        for component in self.components.values():
            names.extend(component.arguments)
        for section in self.sections.values():
            names.extend(section.arguments)

        return list(dict.fromkeys(names))

    def validate(self, conf: dict, path: str) -> dict:
        """
        Validate the fixed sections and dynamic components in a group.
        :param conf: Group configuration to validate.
        :param path: Dotted path of the group.
        :return: Validated group configuration with section defaults applied.
        :raises ConfigurationError: If the group or one of its entries is invalid.
        """
        if not isinstance(conf, dict):
            raise ConfigurationError('Expected dict', path)

        validated = {}
        for entry_name, entry_values in conf.items():
            entry_path = _join_path(path, entry_name)
            validated[entry_name] = self._validate_entry(entry_name, entry_values, entry_path)

        for section_name, section in self.sections.items():
            if section_name in validated:
                continue

            section_values = section.validate({}, _join_path(path, section_name))
            if section_values:
                validated[section_name] = section_values

        return validated

    def _validate_entry(self, name: str, values: dict, path: str) -> dict:
        """
        Validate one fixed section or dynamic component entry.
        :param name: Name of the section or component instance.
        :param values: Entry configuration to validate.
        :param path: Dotted path of the entry.
        :return: Validated section or component configuration.
        :raises ConfigurationError: If the entry structure, type, or properties are invalid.
        """
        if not isinstance(values, dict):
            raise ConfigurationError('Expected dict', path)

        if name in self.sections:
            return self.sections[name].validate(values, path)

        if 'type' not in values:
            raise ConfigurationError('Missing required value', f'{path}.type')

        component_type = values['type']
        try:
            schema = self.components[component_type]
        except (KeyError, TypeError) as error:
            raise ConfigurationError(f'Unknown component type "{component_type}"', f'{path}.type') from error

        component_values = {name: value for name, value in values.items() if name != 'type'}
        return {
            'type': component_type,
            **schema.validate(component_values, path),
        }


class ConfigurationSchema(ConfigurationSectionSchema):
    """
    Schema and validation rules for a complete PowerAPI configuration.
    """

    def __init__(self, separator_env_vars_names: str = '_', separator_args_names: str = '-') -> None:
        """
        Initialize a complete configuration schema.
        :param separator_env_vars_names: Separator used in environment-variable names.
        :param separator_args_names: Separator used in canonical configuration property names.
        """
        super().__init__()
        self.groups: dict[str, ComponentGroupSchema] = {}
        self.arguments_prefix: list[str] = []
        self.default_separator_env_vars_names = separator_env_vars_names
        self.default_separator_args_names = separator_args_names

    def add_argument(
        self,
        name: str,
        *,
        is_flag: bool = False,
        default_value: Any = None,
        help_text: str = '',
        argument_type: type = str,
        is_mandatory: bool = False,
    ) -> None:
        """
        Register a root configuration property.
        :param name: Configuration property name.
        :param is_flag: Whether the property represents a boolean flag.
        :param default_value: Value used when the property is omitted.
        :param help_text: User-facing description of the property.
        :param argument_type: Type used to cast non-flag values.
        :param is_mandatory: Whether the property must be defined.
        :raises ValueError: If the name is already registered as a property or group.
        """
        if name in self.groups:
            raise ValueError(f'Configuration name "{name}" is already registered as a group')

        super().add_argument(
            name,
            is_flag=is_flag,
            default_value=default_value,
            help_text=help_text,
            argument_type=argument_type,
            is_mandatory=is_mandatory,
        )

    def add_group(self, name: str, help_text: str = '', prefix: str = '') -> None:
        """
        Register a top-level configuration group.
        :param name: Configuration name of the group.
        :param help_text: User-facing description of the group.
        :param prefix: Environment-variable prefix assigned to the group.
        :raises ValueError: If the name is already registered as a property or group.
        """
        if name in self.groups:
            raise ValueError(f'Configuration group "{name}" is already registered')
        if name in self.arguments:
            raise ValueError(f'Configuration name "{name}" is already registered as a property')

        self.groups[name] = ComponentGroupSchema(name, help_text, prefix)

    def add_component(self, group_name: str, component: ComponentSchema) -> None:
        """
        Register a component schema in an existing group.
        :param group_name: Group receiving the component schema.
        :param component: Component schema to register.
        :raises ValueError: If the group is unknown or the component type is already registered in it.
        """
        if group_name not in self.groups:
            raise ValueError(f'Configuration group "{group_name}" is not registered')

        group = self.groups[group_name]
        if component.name in group.components:
            raise ValueError(f'Component type "{component.name}" is already registered in group "{group_name}"')

        group.components[component.name] = component

    def add_section(self, group_name: str, section_name: str, section: ConfigurationSectionSchema) -> None:
        """
        Register a fixed configuration section in an existing group.
        :param group_name: Group receiving the configuration section.
        :param section_name: Name identifying and reserving the section in the group.
        :param section: Configuration section schema to register.
        :raises ValueError: If the group is unknown or the section name is already registered in it.
        """
        if group_name not in self.groups:
            raise ValueError(f'Configuration group "{group_name}" is not registered')

        group = self.groups[group_name]
        if section_name in group.sections:
            raise ValueError(f'Configuration section "{section_name}" is already registered in group "{group_name}"')

        group.sections[section_name] = section

    def add_argument_prefix(self, argument_prefix: str) -> None:
        """
        Register a non-overlapping root environment-variable prefix.
        :param argument_prefix: Environment-variable prefix to register.
        :raises ValueError: If the prefix overlaps an existing prefix.
        """
        for existing_prefix in self.arguments_prefix:
            if argument_prefix.startswith(existing_prefix) or existing_prefix.startswith(argument_prefix):
                raise ValueError(f'Environment prefix "{argument_prefix}" conflicts with "{existing_prefix}"')

        self.arguments_prefix.append(argument_prefix)

    def validate(self, conf: dict, path: str = '') -> dict:
        """
        Validate the complete nested configuration against the registered schema.
        :param conf: Merged configuration to validate.
        :param path: Dotted path prepended to configuration errors.
        :return: Canonical validated configuration with defaults applied.
        :raises ConfigurationError: If any root, section, or component configuration value is invalid.
        """
        if not isinstance(conf, dict):
            raise ConfigurationError('Expected dict', path or None)

        root_values = {name: value for name, value in conf.items() if name not in self.groups}
        validated = super().validate(root_values, path)

        for group_name, group in self.groups.items():
            group_path = _join_path(path, group_name)
            validated_group = group.validate(conf.get(group_name, {}), group_path)

            if validated_group or group_name in conf:
                validated[group_name] = validated_group

        return validated


def cast_argument_value(path: str, value: Any, argument: ArgumentDefinition) -> Any:
    """
    Cast one value according to its property definition.
    :param path: Dotted path of the property being cast.
    :param value: Raw configuration value.
    :param argument: Definition describing the expected type.
    :return: Value cast to the declared type.
    :raises ConfigurationError: If the value cannot be cast to the declared type.
    """
    try:
        if isinstance(value, argument.argument_type):
            return value
        if argument.argument_type is bool and isinstance(value, str):
            return string_to_bool(value)
        if argument.argument_type is list and isinstance(value, str):
            return string_to_list(value)
        return argument.argument_type(value)
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f'Expected {argument.argument_type.__name__}', path) from error


def _join_path(path: str, property_name: str) -> str:
    """
    Append a property name to a configuration path.
    :param path: Existing dotted configuration path, or an empty string for the root.
    :param property_name: Property segment to append.
    :return: Combined dotted path.
    """
    return f'{path}.{property_name}' if path else property_name
