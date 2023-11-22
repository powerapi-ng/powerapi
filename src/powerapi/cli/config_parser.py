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
import getopt
import json
import os
import sys
from typing import Any, Callable

from powerapi.exception import AlreadyAddedArgumentException, UnknownArgException, \
    MissingValueException, BadContextException, TooManyArgumentNamesException, NoNameSpecifiedForSubgroupException, \
    SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, BadTypeException, \
    MissingArgumentException, SameLengthArgumentNamesException, InvalidPrefixException, RepeatedArgumentException, \
    SubgroupDoesNotExistException, AlreadyAddedSubgroupException
from powerapi.utils.cli import find_longest_string_in_list, remove_first_characters, string_to_bool


def store_val(argument_name: str, val: Any, configuration: dict, args: list = None) -> (list, dict):
    """
    Action that stores the value of the argument on the parser result

    """
    if val == '':
        val = None

    configuration[argument_name] = val
    return args, configuration


def store_true(argument_name: str, configuration: dict, val: Any = None, args: list = None) -> (list, dict):
    """
    Action that stores a True boolean value on the parser result

    """
    val = True
    configuration[argument_name] = val
    return args, configuration


class ConfigurationArgument:
    """
    Argument provided by a formula configuration.
    """

    def __init__(self, names: list, is_flag: bool, default_value: Any, help_text: str, argument_type: type,
                 is_mandatory: bool, action: Callable = None):
        self.names = names
        self.is_flag = is_flag
        self.default_value = default_value
        self.help_text = help_text
        self.type = argument_type
        self.is_mandatory = is_mandatory
        self.action = action

    def __eq__(self, arg):
        names_ok = True

        for current_name in self.names:
            names_ok = current_name in arg.names

        return names_ok and len(self.names) == len(arg.names) and self.is_flag == arg.is_flag and \
            self.type == arg.type and self.default_value == arg.default_value and \
            self.help_text == arg.help_text and self.is_mandatory == arg.is_mandatory


class BaseConfigParser:
    """"""

    def __init__(self):
        self.arguments = {}

    def add_argument(self, *names, is_flag: bool = False, action: Callable = store_val, default_value: Any = None,
                     help_text: str = '', argument_type: type = str, is_mandatory: bool = False):
        """add an optional argument to the parser that will activate an action

        :param str names: names of the optional argument that will be bind to
                           the action (could be long or short name)

        :param bool is_flag: True if the argument doesn't require to be followed
                           by a value

        :param Callable action: action that will be executed when the argument is
                              caught by the parser. the lambda take 4 parameters
                              (the name of the argument caught by the parser,
                              the value attached to this argument, the current
                              list of arguments that is parsed by the parser and
                              the parser result) and return a list of token and
                              a parser result(dict)

        :param default_value: the default value attached to this argument

        :param str help_text: text that describe the argument

        :param type argument_type: type of the value that the argument must catch

        :param bool is_mandatory: True if the argument is required

        :raise AlreadyAddedArgumentException: when attempting to add an
                                               argument that already have been
                                               added to this parser

        """
        for name in names:
            if name in self.arguments:
                raise AlreadyAddedArgumentException(name)

        argument = ConfigurationArgument(names=list(names), is_flag=is_flag, action=action,
                                         default_value=default_value, help_text=help_text,
                                         argument_type=argument_type, is_mandatory=is_mandatory)

        for name in names:
            self.arguments[name] = argument

    def _get_default_arguments_values(self):
        default_values = {}
        for _, argument in self.arguments.items():
            if argument.default_value is not None:
                argument_name = find_longest_string_in_list(argument.names)
                if argument_name not in default_values:
                    default_values[argument_name] = argument.default_value

        return default_values

    def _get_default_argument_value(self, argument_name: str) -> dict:
        """
        Return a dict containing the default value for the given argument or an empty dict
        if it does not have one or if it does not exist.
        :param str argument_name : The name of the argument
        """
        default_values_dict = {}
        if argument_name in self.arguments:
            argument = self.arguments[argument_name]
            if argument.default_value is not None:
                longest_argument_name = find_longest_string_in_list(argument.names)
                default_values_dict[longest_argument_name] = argument.default_value

        return default_values_dict

    def _get_arguments_str(self, indent: str) -> str:
        already_added_argument = []
        arguments_str_representation = ''
        for _, argument in self.arguments.items():
            if argument not in already_added_argument:
                arguments_str_representation += indent + ', '.join(
                    map(lambda x: '-' + x if len(x) == 1 else '--' + x, argument.names))
                arguments_str_representation += ' : ' + argument.help_text + '\n'
                already_added_argument.append(argument)
        return arguments_str_representation

    def _unknown_argument_behaviour(self, arg_name: str, val: Any, args: list, configuration: dict):
        raise NotImplementedError()

    def _parse(self, args: list, configuration: dict) -> (list, dict):

        while args:
            arg, val = args.pop(0)
            if arg not in self.arguments:
                args.insert(0, (arg, val))
                return self._unknown_argument_behaviour(arg, val, args, configuration)

            argument = self.arguments[arg]

            arg_long_name = find_longest_string_in_list(argument.names)
            val = cast_argument_value(arg_long_name, val, argument)

            args, configuration = argument.action(argument_name=arg_long_name, val=val, args=args,
                                                  configuration=configuration)

        return args, configuration

    def _get_mandatory_arguments(self) -> list:
        """
        Return the list of mandatory arguments
        """
        mand_args = []
        for _, argument in self.arguments.items():
            if argument.is_mandatory and argument not in mand_args:
                mand_args.append(argument)
        return mand_args

    def get_arguments(self):
        """ Get the parser arguments """
        return self.arguments

    def get_longest_arguments_names(self) -> list:
        """
        Return a list with the longest names of the different arguments
        """
        long_arguments_names = []
        for _, argument in self.arguments.items():
            longest_name = find_longest_string_in_list(argument.names)
            if longest_name not in long_arguments_names:
                long_arguments_names.append(longest_name)

        return long_arguments_names

    def validate(self, conf: dict) -> dict:
        """
        Check that mandatory arguments are present in the provided configuration.
        Check that arguments are not repeated in the provided configuration.
        Check that arguments are recognized by the parser.
        It also defines default values if any for arguments that are not defined in the configuration

        """
        # Check that all the mandatory arguments are present
        mandatory_args = self._get_mandatory_arguments()
        for arg in mandatory_args:
            is_present = False
            for arg_name in arg.names:
                if arg_name in conf:
                    is_present = True
                    break
            if not is_present:
                raise MissingArgumentException(str(arg.names))

        # Define default values for no defined arguments if they are specified
        for argument_name, argument_definition in self.arguments.items():
            is_defined = False
            for name in argument_definition.names:
                if name in conf:
                    is_defined = True
                    break
            if not is_defined and argument_definition.default_value is not None:
                conf[argument_name] = argument_definition.default_value

        # Check that arguments are not repeated and that they exist
        present_arguments = []
        for current_argument_name in conf:
            if current_argument_name in self.arguments:
                argument = self.arguments[current_argument_name]
                if argument in present_arguments:
                    raise RepeatedArgumentException(argument_name=current_argument_name)
                present_arguments.append(argument)
            elif current_argument_name != 'type':
                raise UnknownArgException(argument_name=current_argument_name)

        return self.normalize_configuration(conf=conf)

    def normalize_configuration(self, conf: dict) -> dict:
        """
        Return a configuration dict that has all the arguments' names in the long form.
        If an argument does not exist, a UnknownArgException is raised
        If an argument is repeated, a RepeatedArgumentException is raised
        """
        conf_with_long_names = {}

        for current_argument_name in conf:
            if current_argument_name not in self.arguments and current_argument_name != 'type':
                raise UnknownArgException(current_argument_name)

            longest_argument_name = 'type'
            if current_argument_name != 'type':
                current_argument = self.arguments[current_argument_name]
                longest_argument_name = find_longest_string_in_list(current_argument.names)
            if longest_argument_name in conf_with_long_names:
                raise RepeatedArgumentException(argument_name=longest_argument_name)
            conf_with_long_names[longest_argument_name] = conf[current_argument_name]

        return conf_with_long_names

    def cast_arguments_values(self, arguments: dict) -> dict:
        """
        Cast to the argument type the different values in the provided dictionary.
        The dictionary only contains values with basic types (string, int...)
        :param dict arguments: The dictionary with the values to cast
        """
        for argument_name, argument_value in arguments.items():

            if argument_name != 'type':
                casted_value = cast_argument_value(val=argument_value, arg_name=argument_name,
                                                   argument=self.arguments[argument_name])
                arguments[argument_name] = casted_value

        return arguments


class SubgroupParserGroup:
    """
    Group of subgroup parsers stored in a dictionary. Each subgroup has a name
    """

    def __init__(self, group_name: str, help_text: str = '', prefix: str = ''):
        """
        Create a group of subgroup parsers
        :param str group_name: name of the subgroup
        :param str help_text: Help text related to the subgroup
        :param str prefix: Prefix related to the group for parsing environment variables
        """
        self.group_name = group_name
        self.help_text = help_text
        self.subparsers = {}
        self.prefix = prefix

    def get_prefix(self) -> str:
        """
        Return the group's prefix
        """
        return self.prefix

    def contains(self, name: str):
        """
        Check if the given name belongs to one of the subparser of the grouo
        :param str name: Name to look for
        """
        return name in self.subparsers

    def add_subgroup_parser(self, name: str, subparser: BaseConfigParser):
        """
        Add a subgroup parser to the group
        :param str name: Subgroup parser name
        :param BaseConfigParser subparser: subparser to be added
        """
        self.subparsers[name] = subparser

    def get_subgroup_parser(self, name: str) -> BaseConfigParser:
        """
        Return the subgroup parser with the given name
        :param str name: Subparser name
        """
        return self.subparsers[name]

    def __iter__(self):
        return iter(self.subparsers.items())

    def get_help(self) -> str:
        """
        return help string
        """
        help_str = self.group_name + ' details :\n'
        for subparser_name, subparser in self.subparsers.items():
            help_str += '  --' + self.group_name + ' ' + subparser_name + ':\n'
            help_str += subparser.get_help()
            help_str += '\n'

        return help_str

    def get_longest_arguments_names(self) -> list:
        """
        Return a list of arguments names from the different parsers that are part of the group
        """
        arguments_names = []
        for _, subparser in self.subparsers.items():
            arguments_names.extend(subparser.get_longest_arguments_names())
        return list(set(arguments_names))

    def get_group_name(self) -> str:
        """
        Return the name of the group
        """
        return self.group_name


class SubgroupConfigParser(BaseConfigParser):
    """
    A parser for a subgroup
    """

    def __init__(self, name: str):
        """
        Create a subgroup parser with the given name
        :param str name: Name of the subgroup parser
        """
        BaseConfigParser.__init__(self)
        self.name = name

    def _unknown_argument_behaviour(self, arg_name: str, val: Any, args: list,
                                    configuration: dict):
        return args, configuration

    def parse(self, token_list: list) -> (list, dict):
        """
        Parse the given token list until an unknown argument is caught

        :param list token_list: the token list currently parsed

        :return dict: the result of the parsing

        """
        local_result = BaseConfigParser._get_default_argument_value(self, argument_name='name')
        if not token_list:
            return token_list, local_result

        return self._parse(token_list, local_result)

    def get_help(self) -> str:
        """
        return help string
        """
        return self._get_arguments_str('    ')


class RootConfigParser(BaseConfigParser):
    """"""

    def __init__(self, help_arg: bool = True, separator_env_vars_names: str = '_', separator_args_names: str = '-'):
        """
        :param bool help_arg: if True, add a -h/--help argument that display help
        :param str separator_env_vars_names: separator for the environment variables names
        :param str separator_args_names: separator for arguments with composed names
        """
        BaseConfigParser.__init__(self)
        self.short_arg = ''
        self.long_arg = []
        self.subgroup_parsers = {}

        self.arguments_prefix = []
        self.default_separator_env_vars_names = separator_env_vars_names
        self.default_separator_args_names = separator_args_names

        self.help_arg = help_arg
        if help_arg:
            self.add_argument('h', 'help', is_flag=True, argument_type=bool)

    def get_help(self):
        """
        return help string
        """
        s = 'main arguments:\n'
        s += self._get_arguments_str('  ')
        s += '\n'

        for _, subparser_group in self.subgroup_parsers.items():
            s += subparser_group.get_help()

        return s

    def parse(self, args: list) -> dict:
        """
        :param list args: list that contains the arguments and their values

        :return dict: Dictionary that contains the arguments with its associated values extracted from args

        :raise UnknownArgException: when the parser catch an argument that
                                   this parser can't handle

        :raise BadContextException: when an argument that the parser can't
                                    handle in the current context is caught

        :raise MissingValueException: when an argument that require a value is
                                      caught without its value

        :raise BadTypeException: when an argument is parsed with a value of an
                                 incorrect type
        """
        try:
            args, _ = getopt.getopt(args, self.short_arg, self.long_arg)
        except getopt.GetoptError as exn:
            if 'recognized' in exn.msg:
                raise UnknownArgException(exn.opt) from exn
            elif 'requires' in exn.msg:
                raise MissingValueException(exn.opt) from exn

        # remove minus
        args = list(map(lambda x: (remove_first_characters(x[0]), x[1]), args))

        # verify if help argument exists in args
        if self.help_arg:
            for arg_name, _ in args:
                if arg_name in ('h', 'help'):
                    print(self.get_help())
                    sys.exit(0)

        configuration = {}

        args, configuration = self._parse(args, configuration)

        return configuration

    def parse_config_dict(self, file_name: str) -> dict:
        """
        Return a configuration dict that has all the arguments' names in the long form.
        If an argument does not exist, a UnknownArgException is raised
        """
        config_file = open(file_name, 'r')
        conf = json.load(config_file)
        return self.normalize_configuration(conf=conf)

    def normalize_configuration(self, conf: dict) -> dict:
        """
        Return a configuration dict that has all the arguments' names in the long form.
        If an argument does not exist, a UnknownArgException is raised
        """
        # We normalize the simple arguments names
        conf = BaseConfigParser.normalize_configuration(self, conf=conf)

        # We normalize the groups arguments names

        for argument_name, argument_value in conf.items():
            if isinstance(argument_value, dict):
                for group_name, group in argument_value.items():
                    group = self.subgroup_parsers[argument_name].get_subgroup_parser(name=group['type']). \
                        normalize_configuration(conf=group)
                    argument_value[group_name] = group

        return conf

    def _unknown_argument_behaviour(self, arg_name: str, val: Any, args: list,
                                    configuration: dict):
        good_contexts = []
        for main_arg_name, subparser_group in self.subgroup_parsers.items():
            for subparser_name, subparser in subparser_group:
                if arg_name in subparser.arguments:
                    good_contexts.append((main_arg_name, subparser_name))
        raise BadContextException(arg_name, good_contexts)

    def _add_argument_names(self, names: list, is_flag: bool):

        if len(names) > 2:
            raise TooManyArgumentNamesException(names[2])

        if len(names) > 1 and len(names[0]) == len(names[1]):
            raise SameLengthArgumentNamesException(names[1])

        def add_suffix_to_argument_name_if_required(current_name):
            if len(current_name) == 1:
                return current_name + ('' if is_flag else ':')
            return current_name + ('' if is_flag else '=')

        for name in names:
            if len(name) == 1:
                self.short_arg += add_suffix_to_argument_name_if_required(name)
            else:
                self.long_arg.append(add_suffix_to_argument_name_if_required(name))

    def add_argument(self, *names, is_flag: bool = False, action: Callable = store_val, default_value: Any = None,
                     help_text: str = '', argument_type: type = str, is_mandatory: bool = False):
        self._add_argument_names(list(names), is_flag)
        BaseConfigParser.add_argument(self, *names, is_flag=is_flag, action=action, default_value=default_value,
                                      help_text=help_text, argument_type=argument_type, is_mandatory=is_mandatory)

    def add_subgroup_parser(self, subgroup_type: str, subgroup_parser: SubgroupConfigParser):
        """
        Add a subparser that will be used by the argument *group_name*
        The group must contain a name action
        :param str subgroup_type: the group type
        :param SubgroupConfigParser subgroup_parser: The subgroup parser
        :param str help_text: help text related to the parser

        :raise AlreadyAddedArgumentException: when attempting to add an
                                              argument that already have been
                                              added to this parser
        :raise SubgroupDoesNotExistException If the group related to the paser does not exist
        """

        if 'name' not in subgroup_parser.arguments:
            raise SubgroupParserWithoutNameArgumentException()
        if subgroup_type not in self.subgroup_parsers:
            raise SubgroupDoesNotExistException(argument_name=subgroup_type)
        else:
            if self.subgroup_parsers[subgroup_type].contains(subgroup_parser.name):
                raise AlreadyAddedArgumentException(subgroup_parser.name)

        self.subgroup_parsers[subgroup_type].add_subgroup_parser(subgroup_parser.name, subgroup_parser)

        for action_name, action in subgroup_parser.arguments.items():
            self._add_argument_names([action_name], action.is_flag)

    def add_subgroup(self, subgroup_type: str, help_text: str = '', prefix: str = ''):
        """
        Add a subgroup that will be used by the argument *group_name*
        The group must contain a name action
        :param str subgroup_type: the subgroup type
        :param str help_text: help text related to the subgroup
        :param str prefix: the prefix related to the subgroup

        :raise AlreadyAddedSubgroupException is the subgroup already exists
        """

        def _action(argument_name: str, val: Any, args: list, configuration: dict):
            if argument_name not in configuration:
                configuration[argument_name] = {}

            parser = self.subgroup_parsers[argument_name].get_subgroup_parser(val)
            args, parse_result = parser.parse(args)

            if 'name' not in parse_result:
                raise NoNameSpecifiedForSubgroupException(subgroup_type)

            subgroup_name = parse_result['name']
            del parse_result['name']

            if subgroup_name in configuration[argument_name]:
                raise SubgroupAlreadyExistException(subgroup_name)

            configuration[argument_name][subgroup_name] = parse_result
            configuration[argument_name][subgroup_name]['type'] = parser.name

            return args, configuration

        if subgroup_type not in self.subgroup_parsers:
            self.subgroup_parsers[subgroup_type] = SubgroupParserGroup(subgroup_type, help_text=help_text,
                                                                       prefix=prefix)
            self.add_argument(subgroup_type, action=_action, help_text=help_text)

        else:
            raise AlreadyAddedSubgroupException(subgroup_type)

    def add_argument_prefix(self, argument_prefix: str):
        """
        Add a simple argument prefix to the list if argument_prefix is no prefix of an existing argument prefix or
        vice-versa. Otherwise, it raises an InvalidPrefixException
        :param argument_prefix: a new argument prefix to be added
        """
        for existing_argument_prefix in self.arguments_prefix:
            if argument_prefix.startswith(existing_argument_prefix) or \
                    existing_argument_prefix.startswith(argument_prefix):
                raise InvalidPrefixException(existing_prefix=existing_argument_prefix, new_prefix=argument_prefix)

        self.arguments_prefix.append(argument_prefix)

    def parse_config_environment_variables(self) -> dict:
        """
        Parse environment variables to extract a configuration. Then merges the extracted configution with the one
        provided as parameter
        :param dict current_conf: Configuration to execute the merge
        """

        conf = {}

        for current_environment_var_prefix in self.arguments_prefix:
            conf = self._extract_simple_environment_variables_with_prefix(
                simple_variables_prefix=current_environment_var_prefix,
                groups_variables_prefix=self.get_groups_prefixes())
            # We normalize the arguments names
            conf = self.normalize_configuration(conf=conf)

            # We cast every value in conf to the correct type
            conf = self.cast_arguments_values(arguments=conf)

        groups_names = []
        for _, group in self.subgroup_parsers.items():

            group_name = group.get_group_name()
            group_conf = self._extract_group_environment_variables(group=group)
            if len(group_conf) > 0:
                conf[group_name] = group_conf
                groups_names.append(group_name)

        for group_name in groups_names:
            for subgroup_name, subgroup_arguments in conf[group_name].items():
                # We normalize the names in each group. The argument type for each subgroup
                # is required
                if 'type' not in subgroup_arguments:
                    raise MissingArgumentException(argument_name=group_name + '>' + subgroup_name + '>' + 'type')
                subgroup_parser = self.subgroup_parsers[group_name].get_subgroup_parser(name=subgroup_arguments['type'])
                subgroup_arguments = subgroup_parser.normalize_configuration(conf=subgroup_arguments)

                # We cast every value in subgroup_arguments to the correct type
                subgroup_arguments = subgroup_parser.cast_arguments_values(arguments=subgroup_arguments)
                conf[group_name][subgroup_name] = subgroup_arguments

        return conf

    def get_groups_prefixes(self) -> list:
        """
        Return a list with the prefixes of different groups
        """
        prefixes = []
        for _, subgroup in self.subgroup_parsers.items():
            prefixes.append(subgroup.get_prefix())

        return prefixes

    def _extract_group_name_from_prefix(self, prefix: str) -> str:
        """
        Extract the group name from the given prefix. It assumes the words in the prefix
        are separated by self.default_separator_env_vars_names and the group name is composed by a single word

        """
        # prefix.split = ['<prefix-begining>', '<group-name>', '']
        return prefix.split(self.default_separator_env_vars_names)[1].lower()

    def _extract_simple_environment_variables_with_prefix(self, simple_variables_prefix: str,
                                                          groups_variables_prefix: list) -> dict:
        """
        Extract from environment variables the ones starting with prefix and that do not belong to groups.
        The returned dictionary contains the variables names as keys without prefix and in lower case
        :param str simple_variables_prefix: Prefix to extract the simple environment variables
        :param list groups_variables_prefix: List of group prefix for identifying simple variables
        """
        simple_variables_with_prefix = {}
        for var_name in os.environ:
            is_group_variable = False
            for group_variable_prefix in groups_variables_prefix:
                if var_name.startswith(group_variable_prefix):
                    is_group_variable = True
                    break
            if not is_group_variable and var_name.startswith(simple_variables_prefix):
                var_name_without_prefix = var_name[len(simple_variables_prefix) - len(var_name):]. \
                    lower().replace(self.default_separator_env_vars_names, self.default_separator_args_names)
                simple_variables_with_prefix[var_name_without_prefix] = os.environ[var_name]
        return simple_variables_with_prefix

    def _extract_group_environment_variables(self, group: SubgroupParserGroup) -> dict:
        """
        Extract from environment variables the ones starting with group_prefix.
        The returned dictionary contains the variables names as keys without prefix and in lower case
        :param str group_prefix: Prefix to extract the group environment variables
        :param list subgroups_variables_names: List of variables names related to the group
        """
        group_variables_with_prefix = {}
        group_prefix = group.get_prefix()
        subgroups_arguments_names = group.get_longest_arguments_names()
        subgroups_arguments_names.append('type')
        for environ_var_name in os.environ:
            if environ_var_name.startswith(group_prefix):
                # We remove the prefix and put the name in lower case
                suffix_environ_var_name = environ_var_name[len(group_prefix) - len(environ_var_name):]. \
                    lower().replace(self.default_separator_env_vars_names, self.default_separator_args_names)
                for group_variable_name in subgroups_arguments_names:
                    group_variable_name_lower_case = group_variable_name. \
                        lower().replace(self.default_separator_env_vars_names, self.default_separator_args_names)

                    # The group_variable_name_lower_case has to be at the end of the suffix
                    if suffix_environ_var_name.endswith(group_variable_name_lower_case) and \
                            suffix_environ_var_name[
                                suffix_environ_var_name.rfind(group_variable_name_lower_case) - 1] == \
                            self.default_separator_args_names:
                        # The subgroup's name is at the beginning of the suffix
                        subgroup_name = suffix_environ_var_name[0:
                                                                suffix_environ_var_name.rfind(
                                                                    group_variable_name_lower_case) - 1]

                        if subgroup_name not in group_variables_with_prefix:
                            group_variables_with_prefix[subgroup_name] = {}
                        group_variables_with_prefix[subgroup_name][group_variable_name_lower_case] = os.environ[
                            environ_var_name]
                        break

        return group_variables_with_prefix


def cast_argument_value(arg_name: str, val: Any, argument: ConfigurationArgument):
    """
    Cast the given value to argument.type
    :param str arg_name: The argument name
    :param Any val: Current value given to the argument
    :param ConfigurationAgument argument: The argument definition
    """
    try:
        if argument.type is bool and val is not None and isinstance(val, str):
            return string_to_bool(val)
        return argument.type(val)
    except ValueError as exn:
        raise BadTypeException(arg_name, argument.type) from exn
    return val
