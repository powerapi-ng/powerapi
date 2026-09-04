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
from dataclasses import dataclass

from powerapi.cli.config_parser import (
    ArgumentDefinition,
    ComponentGroupSchema,
    ComponentSchema,
    ConfigurationSchema,
    ConfigurationSectionSchema,
)
from powerapi.exception import PowerAPIExceptionWithMessage

_CONFIG_ASSIGNMENTS_DEST = '_powerapi_config_assignments'
_CONFIG_FILE_DEST = '_powerapi_config_file'


class CLIParseException(PowerAPIExceptionWithMessage):
    """
    Exception raised when command-line arguments cannot be parsed.
    """


@dataclass(frozen=True)
class ConfigAssignment:
    """
    Raw value associated with a hierarchical configuration path.
    """
    path: tuple[str, ...]
    value: str


@dataclass(frozen=True)
class CLIParseResult:
    """
    Configuration values and configuration file selected on the CLI.
    """
    configuration: dict
    config_file: str | None


@dataclass(frozen=True)
class _HelpTheme:
    """
    Argparse colors assigned to configuration help elements.
    """
    heading_color: str = ''
    selector_color: str = ''
    path_color: str = ''
    supported_type_color: str = ''
    component_type_color: str = ''
    details_color: str = ''
    reset: str = ''

    def _colorize(self, text: str, color: str) -> str:
        """
        Apply one theme color to text.
        :param text: Text to colorize.
        :param color: ANSI color sequence, or an empty string when colors are disabled.
        :return: Colorized or unchanged text.
        """
        return f'{color}{text}{self.reset}'

    def heading(self, text: str) -> str:
        """
        Colorize a configuration help heading.
        :param text: Heading to colorize.
        :return: Colorized or unchanged heading.
        """
        return self._colorize(text, self.heading_color)

    def selector(self, text: str) -> str:
        """
        Colorize a configuration block selector.
        :param text: Selector to colorize.
        :return: Colorized or unchanged selector.
        """
        return self._colorize(text, self.selector_color)

    def path(self, text: str) -> str:
        """
        Colorize a nested configuration path.
        :param text: Path to colorize.
        :return: Colorized or unchanged path.
        """
        return self._colorize(text, self.path_color)

    def supported_type(self, text: str) -> str:
        """
        Colorize a supported component type.
        :param text: Component type to colorize.
        :return: Colorized or unchanged component type.
        """
        return self._colorize(text, self.supported_type_color)

    def component_type(self, text: str) -> str:
        """
        Colorize a selected component type.
        :param text: Component type to colorize.
        :return: Colorized or unchanged component type.
        """
        return self._colorize(text, self.component_type_color)

    def details(self, text: str) -> str:
        """
        Colorize configuration argument details.
        :param text: Details to colorize.
        :return: Colorized or unchanged details.
        """
        return self._colorize(text, self.details_color)


def _parse_assignment(expression: str) -> ConfigAssignment:
    """
    Parse a dotted ``PATH=VALUE`` configuration assignment.
    :param expression: Assignment expression to parse.
    :return: Parsed configuration path and raw value.
    :raises CLIParseException: If the expression does not contain a valid supported path.
    """
    path_expression, separator, value = expression.partition('=')
    if separator == '':
        raise CLIParseException(f'Invalid configuration assignment "{expression}": expected PATH=VALUE')

    path = tuple(path_expression.split('.'))
    if any(segment == '' for segment in path):
        raise CLIParseException(f'Invalid configuration assignment "{expression}": path contains an empty segment')
    if len(path) not in (1, 3):
        raise CLIParseException(f'Invalid configuration assignment "{expression}": expected PROPERTY or GROUP.COMPONENT.PROPERTY')

    return ConfigAssignment(path=path, value=value)


def _apply_assignment(configuration: dict, assignment: ConfigAssignment) -> None:
    """
    Apply an assignment to a nested configuration.
    :param configuration: Configuration to update.
    :param assignment: Parsed assignment to apply.
    :raises CLIParseException: If the assignment conflicts with an existing path.
    """
    target = configuration
    dotted_path = '.'.join(assignment.path)

    for segment in assignment.path[:-1]:
        target = target.setdefault(segment, {})
        if not isinstance(target, dict):
            raise CLIParseException(f'Conflicting configuration path: "{dotted_path}"')

    property_name = assignment.path[-1]
    if isinstance(target.get(property_name), dict):
        raise CLIParseException(f'Conflicting configuration path: "{dotted_path}"')

    target[property_name] = assignment.value


def _build_configuration(expressions: list[str]) -> dict:
    """
    Build a nested configuration dictionary from dotted assignments.
    :param expressions: Assignment expressions ordered as they appeared on the command line.
    :return: Nested configuration containing the assigned raw values.
    :raises CLIParseException: If an expression is invalid or conflicts with another path.
    """
    configuration = {}

    for expression in expressions:
        _apply_assignment(configuration, _parse_assignment(expression))

    return configuration


def _get_argument_definitions(schema: ConfigurationSectionSchema) -> list[ArgumentDefinition]:
    """
    Return each argument definition once in registration order.
    :param schema: Configuration section containing the arguments.
    :return: Canonical argument definitions.
    """
    return list(schema.arguments.values())


def _get_argparse_theme() -> _HelpTheme:
    """
    Return argparse's active color theme when its expected layout is available.
    :return: Active argparse theme, or a plain-text fallback.
    """
    formatter = argparse.RawDescriptionHelpFormatter('')
    try:
        theme = getattr(formatter, '_theme')  # noqa: B009
        return _HelpTheme(
            heading_color=theme.heading,
            selector_color=theme.long_option,
            path_color=theme.summary_long_option,
            supported_type_color=theme.summary_action,
            component_type_color=theme.action,
            details_color=theme.summary_label,
            reset=theme.reset,
        )
    except AttributeError:
        return _HelpTheme()


def _format_argument_help(argument: ArgumentDefinition, theme: _HelpTheme) -> str:
    """
    Format the description and constraints of a configuration argument.
    :param argument: Argument definition to describe.
    :param theme: Active argparse color theme.
    :return: Human-readable argument help.
    """
    details = [argument.argument_type.__name__]
    if argument.is_mandatory:
        details.append('required')
    elif argument.default_value is not None:
        details.append(f"default: {argument.default_value!r}")

    details_text = theme.details(f'({", ".join(details)})')
    return f'{argument.help_text} {details_text}' if argument.help_text else details_text


def _format_assignment_help(theme: _HelpTheme) -> str:
    """
    Format the supported explicit-assignment syntax.
    :param theme: Active argparse color theme.
    :return: Assignment syntax and examples.
    """
    return '\n'.join([
        theme.heading('configuration assignments:'),
        f'  {theme.path('PROPERTY=VALUE')}',
        f'  {theme.path('GROUP.NAME.PROPERTY=VALUE')}',
        '  Example: -C stream=false -C input.sensor.type=socket -C input.sensor.port=9080',
    ])


def _format_root_arguments_help(schema: ConfigurationSchema, theme: _HelpTheme) -> str:
    """
    Format root configuration paths.
    :param schema: Configuration schema containing the root arguments.
    :param theme: Active argparse color theme.
    :return: Root configuration help, or an empty string when no root arguments are registered.
    """
    arguments = _get_argument_definitions(schema)
    if not arguments:
        return ''

    lines = [theme.heading('root properties:')]
    for argument in arguments:
        lines.append(f'  {theme.path(argument.name)}')
        lines.append(f'    {_format_argument_help(argument, theme)}')

    return '\n'.join(lines)


def _format_component_help(group_name: str, component: ComponentSchema, theme: _HelpTheme) -> str:
    """
    Format configuration paths for one component type.
    :param group_name: Name of the component group.
    :param component: Component schema to describe.
    :param theme: Active argparse color theme.
    :return: Component type assignment and its property paths.
    """
    selector = theme.selector(f'{group_name}.NAME.type')
    component_type = theme.component_type(component.name)
    lines = [f'  {selector}={component_type}']
    for argument in _get_argument_definitions(component):
        path = theme.path(f'{group_name}.NAME.{argument.name}')
        lines.append(f'    {path}')
        lines.append(f'      {_format_argument_help(argument, theme)}')

    return '\n'.join(lines)


def _format_section_help(group_name: str, section_name: str, section: ConfigurationSectionSchema, theme: _HelpTheme) -> str:
    """
    Format configuration paths for one fixed section.
    :param group_name: Name of the configuration group.
    :param section_name: Name of the fixed section.
    :param section: Configuration section schema to describe.
    :param theme: Active argparse color theme.
    :return: Fixed section property paths.
    """
    selector = theme.selector(f'{group_name}.{section_name}')
    lines = [f'  {selector}:']
    for argument in _get_argument_definitions(section):
        path = theme.path(f'{group_name}.{section_name}.{argument.name}')
        lines.append(f'    {path}')
        lines.append(f'      {_format_argument_help(argument, theme)}')

    return '\n'.join(lines)


def _format_group_help(group: ComponentGroupSchema, theme: _HelpTheme) -> str:
    """
    Format configuration paths for a configuration group.
    :param group: Configuration group to describe.
    :param theme: Active argparse color theme.
    :return: Group configuration help, or an empty string when the group has no registered schemas.
    """
    if not group.components and not group.sections:
        return ''

    lines = [theme.heading(f'{group.group_name} configuration:')]

    if group.help_text:
        lines.append(f'  {group.help_text}')

    if group.components:
        selector = theme.selector(f'{group.group_name}.NAME.type')
        supported_types = ', '.join(map(theme.supported_type, group.components))
        lines.append(f'  {selector}')
        lines.append(f'    Supported types: {supported_types}')
        lines.append('')
        lines.append('\n\n'.join(
            _format_component_help(group.group_name, component, theme)
            for component in group.components.values()
        ))

    lines.extend(
        _format_section_help(group.group_name, section_name, section, theme)
        for section_name, section in group.sections.items()
    )

    return '\n'.join(lines)


def _format_configuration_help(schema: ConfigurationSchema) -> str:
    """
    Format assignment paths registered in a configuration schema.
    :param schema: Configuration schema to describe.
    :return: Text appended to the standard argparse help.
    """
    theme = _get_argparse_theme()
    sections = [
        _format_assignment_help(theme),
        _format_root_arguments_help(schema, theme),
        *(_format_group_help(group, theme) for group in schema.groups.values()),
    ]
    return '\n\n'.join(section for section in sections if section)


class CLIArgumentParser:
    """
    Parse ordinary CLI options and repeatable configuration overrides.
    """

    def __init__(self, schema: ConfigurationSchema) -> None:
        """
        Initialize a schema-driven command-line parser.
        :param schema: Configuration schema used to register root options and generate help.
        """
        self._schema = schema

    @staticmethod
    def _add_schema_arguments(argument: ArgumentDefinition, parser: argparse.ArgumentParser) -> None:
        """
        Register one schema argument as a command-line option.
        :param argument: Schema argument to register.
        :param parser: Argument parser receiving the option.
        :raises CLIParseException: If the option conflicts with an existing command-line option.
        """
        kwargs = {
            'default': argparse.SUPPRESS,
            'dest': argument.name,
            'help': argument.help_text,
        }
        if argument.is_flag:
            kwargs['action'] = 'store_true'

        try:
            parser.add_argument(f'--{argument.name}', **kwargs)
        except argparse.ArgumentError as error:
            raise CLIParseException(f'Failed to add argument: {error}') from error

    def _build_parser(self) -> argparse.ArgumentParser:
        """
        Build an argument parser from the current configuration schema.
        :return: Configured argument parser.
        :raises CLIParseException: If schema arguments define conflicting command-line options.
        """
        parser = argparse.ArgumentParser(
            allow_abbrev=False,
            exit_on_error=False,
            epilog=_format_configuration_help(self._schema),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            '--config-file',
            dest=_CONFIG_FILE_DEST,
            metavar='FILE',
            help='Load configuration from a JSON file',
        )

        parser.add_argument(
            '-C', '--set-config',
            action='append',
            default=None,
            dest=_CONFIG_ASSIGNMENTS_DEST,
            metavar='PATH=VALUE',
            help='Set a configuration value using a dotted path; may be repeated',
        )

        for argument in _get_argument_definitions(self._schema):
            self._add_schema_arguments(argument, parser)

        return parser

    def parse(self, args: list[str]) -> CLIParseResult:
        """
        Parse command-line arguments without validating component schemas.
        :param args: Command-line arguments without the executable name.
        :return: Parsed root configuration, dotted assignments, and optional configuration file path.
        :raises CLIParseException: If argparse rejects the arguments or a dotted assignment is invalid.
        """
        parser = self._build_parser()
        try:
            namespace = parser.parse_args(args)
        except argparse.ArgumentError as error:
            raise CLIParseException(f'Failed to parse CLI: {error}') from error

        parsed_arguments = dict(vars(namespace))
        expressions = parsed_arguments.pop(_CONFIG_ASSIGNMENTS_DEST) or []
        config_file = parsed_arguments.pop(_CONFIG_FILE_DEST)

        configuration = _build_configuration(expressions)
        configuration.update(parsed_arguments)

        return CLIParseResult(configuration=configuration, config_file=config_file)
