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

import sys
from typing import Any

from powerapi.cli.cli_parser import CLIArgumentParser
from powerapi.cli.config_loader import EnvironmentConfigLoader, JSONConfigLoader
from powerapi.cli.config_parser import (
    ComponentSchema,
    ConfigurationSchema,
    ConfigurationSectionSchema,
)

from ._utils import merge_dictionaries


class ConfigurationParsingManager:
    """
    Register the schema and orchestrate all configuration sources.
    """

    def __init__(self) -> None:
        self.schema = ConfigurationSchema()
        self.argument_parser = CLIArgumentParser(self.schema)
        self.json_loader = JSONConfigLoader()
        self.environment_loader = EnvironmentConfigLoader(self.schema)

    def add_argument_prefix(self, argument_prefix: str) -> None:
        """
        Register an environment-variable prefix for root properties.
        :param argument_prefix: Environment-variable prefix to register.
        :raises ValueError: If the prefix overlaps an existing prefix.
        """
        self.schema.add_argument_prefix(argument_prefix=argument_prefix)

    def add_group(self, name: str, help_text: str = '', prefix: str = '') -> None:
        """
        Register a configuration group and its environment prefix.
        :param name: Configuration name of the group.
        :param help_text: User-facing description of the group.
        :param prefix: Environment-variable prefix assigned to the group.
        :raises ValueError: If the group name is already registered.
        """
        self.schema.add_group(name, help_text=help_text, prefix=prefix)

    def add_component(self, group_name: str, component: ComponentSchema) -> None:
        """
        Register a component schema in a group.
        :param group_name: Group receiving the component schema.
        :param component: Component schema to register.
        :raises ValueError: If the group is unknown or the component type is already registered.
        """
        self.schema.add_component(group_name, component)

    def add_section(self, group_name: str, section_name: str, section: ConfigurationSectionSchema) -> None:
        """
        Register a fixed configuration section in a group.
        :param group_name: Group receiving the configuration section.
        :param section_name: Name identifying and reserving the section in the group.
        :param section: Configuration section schema to register.
        :raises ValueError: If the group is unknown or the section name is already registered.
        """
        self.schema.add_section(group_name, section_name, section)

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
        Register a root property in the configuration schema.
        :param name: Configuration property name.
        :param is_flag: Whether the option is a boolean flag.
        :param default_value: Value used when the property is omitted.
        :param help_text: Description displayed in command-line help.
        :param argument_type: Type used to cast non-flag values.
        :param is_mandatory: Whether the property must be defined.
        :raises ValueError: If the property name is already registered.
        """
        self.schema.add_argument(
            name,
            is_flag=is_flag,
            default_value=default_value,
            help_text=help_text,
            argument_type=argument_type,
            is_mandatory=is_mandatory,
        )

    def validate(self, conf: dict) -> dict:
        """
        Validate and canonicalize a merged configuration.
        :param conf: Merged configuration to validate.
        :return: Canonical validated configuration with defaults applied.
        :raises ConfigurationError: If the configuration is invalid.
        """
        return self.schema.validate(conf)

    def _parse_configuration_sources(self, cli_line: list[str]) -> dict:
        """
        Load and merge every configuration source.
        :param cli_line: Command-line arguments without the executable name.
        :return: Merged configuration with CLI, environment, then file precedence.
        :raises CLIParseException: If command-line arguments are invalid.
        :raises FileNotFoundError: If the selected JSON configuration file does not exist.
        :raises ConfigurationError: If the selected file does not contain a valid JSON configuration object.
        """
        parsed_cli = self.argument_parser.parse(cli_line)
        parsed_config_file = self.json_loader.load(parsed_cli.config_file)
        parsed_environment = self.environment_loader.load()

        return merge_dictionaries(parsed_config_file, parsed_environment, parsed_cli.configuration)

    def parse(self, args: list[str] | None = None) -> dict:
        """
        Load, merge, and validate configuration values.

        Precedence is CLI, then environment variables, then the JSON file.
        Parsing and validation errors propagate to the application boundary.
        :param args: Command-line arguments including an optional executable name, or None to use ``sys.argv``.
        :return: Merged, canonical, and validated PowerAPI configuration.
        :raises CLIParseException: If command-line arguments are invalid.
        :raises FileNotFoundError: If the selected JSON configuration file does not exist.
        :raises ConfigurationError: If the selected file contains invalid JSON or the merged configuration is invalid.
        """
        if args is None:
            args = sys.argv

        cli_line = args[1:] if args and not args[0].startswith('-') else args
        return self.validate(self._parse_configuration_sources(cli_line))
