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
import os
from collections.abc import Iterable

from powerapi.cli.config_parser import (
    ComponentGroupSchema,
    ConfigurationSchema,
)
from powerapi.exception import ConfigurationError

_EnvironmentItems = Iterable[tuple[str, str]]


class JSONConfigLoader:
    """
    Load partial configuration values from a JSON file.
    """

    def load(self, file_name: str | None) -> dict:
        """
        Load a JSON configuration.
        :param file_name: Path of the JSON file, or None when no configuration file was selected.
        :return: The loaded configuration, or an empty dictionary when no file was selected.
        :raises FileNotFoundError: If the selected file does not exist.
        :raises ConfigurationError: If the input file is invalid.
        """
        if file_name is None:
            return {}

        try:
            with open(file_name, encoding='utf-8') as config_file:
                configuration = json.load(config_file)
        except json.JSONDecodeError as error:
            raise ConfigurationError(f'Invalid JSON in configuration file "{file_name}": {error}') from error

        if not isinstance(configuration, dict):
            raise ConfigurationError('Expected a JSON object')

        return configuration


class EnvironmentConfigLoader:
    """
    Load configuration values using the established PowerAPI environment format.
    """

    def __init__(self, schema: ConfigurationSchema) -> None:
        """
        Initialize an environment configuration loader.
        :param schema: Schema describing the accepted root, section, and component properties.
        """
        self._schema = schema

    def load(self) -> dict:
        """
        Load raw configuration values from the environment.
        :return: The configuration extracted from the current process environment.
        """
        environment = tuple(os.environ.items())
        configuration = self._load_root_configuration(environment)

        for group_name, group in self._schema.groups.items():
            if not group.prefix:
                continue

            group_configuration = self._extract_group_values(group, environment)
            if group_configuration:
                configuration[group_name] = group_configuration

        return configuration

    def _load_root_configuration(self, environment: _EnvironmentItems) -> dict:
        """
        Load root configuration values from an environment snapshot.
        :param environment: Environment variable names and values.
        :return: Raw root configuration values.
        """
        configuration = {}
        group_prefixes = [group.prefix for group in self._schema.groups.values() if group.prefix]

        for prefix in self._schema.arguments_prefix:
            root_values = self._extract_root_values(prefix, group_prefixes, environment)
            configuration.update(root_values)

        return configuration

    def _extract_root_values(self, prefix: str, group_prefixes: list[str], environment: _EnvironmentItems) -> dict:
        """
        Extract root properties belonging to one environment prefix.
        :param prefix: Prefix identifying root configuration variables.
        :param group_prefixes: Prefixes reserved for component groups.
        :param environment: Environment variable names and values.
        :return: Raw root configuration values.
        """
        values = {}
        for variable_name, value in environment:
            if not variable_name.startswith(prefix):
                continue

            if any(variable_name.startswith(group_prefix) for group_prefix in group_prefixes):
                continue

            property_name = self._normalize_name(variable_name[len(prefix):])
            values[property_name] = value

        return values

    def _extract_group_values(self, group: ComponentGroupSchema, environment: _EnvironmentItems) -> dict:
        """
        Extract entry properties belonging to one environment group.
        :param group: Schema of the configuration group.
        :param environment: Environment variable names and values.
        :return: Raw configurations indexed by component or section name.
        """
        values = {}
        normalized_names = sorted((self._normalize_name(name) for name in [*group.get_argument_names(), 'type']), key=len, reverse=True)

        for variable_name, value in environment:
            if not variable_name.startswith(group.prefix):
                continue

            suffix = self._normalize_name(variable_name[len(group.prefix):])
            for property_name in normalized_names:
                marker = f'{self._schema.default_separator_args_names}{property_name}'
                if not suffix.endswith(marker):
                    continue

                component_name = suffix[:-len(marker)]
                if component_name:
                    values.setdefault(component_name, {})[property_name] = value

                break

        return values

    def _normalize_name(self, name: str) -> str:
        """
        Convert an environment name fragment to its configuration spelling.
        :param name: Environment name fragment.
        :return: Lowercase configuration name using the configured argument separator.
        """
        return name.lower().replace(self._schema.default_separator_env_vars_names, self._schema.default_separator_args_names)
