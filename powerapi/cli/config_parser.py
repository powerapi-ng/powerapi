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
import sys
from copy import deepcopy
from typing import Any, Callable, Type

from powerapi.exception import AlreadyAddedArgumentException, UnknownArgException, \
    MissingValueException, BadContextException, TooManyArgumentNamesException, NoNameSpecifiedForGroupException, \
    SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, BadTypeException
from powerapi.utils.cli import find_longest_name, extract_minus

def store_val(arg: str, val: Any, args: list, acc: dict):
    """
    Action that stores the value of the argument on the parser result

    """
    if val == '':
        val = None

    acc[arg] = val
    return args, acc


def store_true(arg: str, _, args: list, acc: dict):
    """
    Action that stores a True boolean value on the parser result

    """
    acc[arg] = True
    return args, acc


class ConfigurationArgument:
    """
    Argument provided by a formula configuration.
    """

    def __init__(self, names: list, is_flag: bool, default_value, help_text: str, argument_type: type,
                 is_mandatory: bool, action: Callable = None):
        self.names = names
        self.is_flag = is_flag
        self.default_value = default_value
        self.help_text = help_text
        self.type = argument_type
        self.is_mandatory = is_mandatory
        self.action = action

class BaseConfigParser:
    """"""
    def __init__(self):
        self.arguments = {}
        self.default_values = {}

    def add_argument(self, *names, is_flag: bool= False, action: Callable=store_val, default_value: Any=None,
                     help_text: str='', argument_type: type=str, is_mandatory: bool= False):
        """add an optional argument to the parser that will activate an action

        :param str *names: names of the optional argument that will be bind to
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
        argument = ConfigurationArgument(names= list(names), is_flag= is_flag, action= action,
                                         default_value= default_value, help_text= help_text,
                                         argument_type= argument_type, is_mandatory=is_mandatory)

        for name in names:
            if name in self.arguments:
                raise AlreadyAddedArgumentException(name)
            self.arguments[name] = argument

        argument_name = find_longest_name(names)

        if default_value is not None:
            self.default_values[argument_name] = default_value

    def _get_arguments_str(self, indent:str)-> str:
        s = ''
        for _, argument in self.arguments:
            s += indent + ', '.join(map(lambda x: '-' + x if len(x) == 1 else '--' + x, argument.names))
            s += ' : ' + argument.help_text + '\n'
        return s

    def _unknown_argument_behaviour(self, arg_name:str, val:Any, args: list, acc: dict):
        raise NotImplementedError()

    def _parse(self, args: list, acc:dict)-> (list, dict):

        while args:
            arg, val = args.pop(0)
            if arg not in self.arguments:
                args.insert(0, (arg, val))
                return self._unknown_argument_behaviour(arg, val, args, acc)

            argument = self.arguments[arg]

            arg_long_name = find_longest_name(argument.names)
            val = cast_argument_value(arg_long_name, val, argument)

            args, acc = argument.action(arg_long_name, val, args, acc)

        return args, acc


    def _get_mandatory_arguments(self):
        """
        Return the list of mandatory arguments
        """
        mand_args = []
        for name, argument in self.arguments.items():
            if argument.is_mandatory:
                mand_args.append(name)
        return mand_args

    def get_arguments(self):
        """ Get the parser arguments """
        return self.arguments

    def validate(self, conf: dict)-> dict:
        """
            Check that mandatory arguments are present in the provided configuration.
            It also defines default values if any for arguments that are not defined in the configuration
        """
        # Check that all the mandatory arguments are precised
        mandatory_args = self._get_mandatory_arguments()
        for arg in mandatory_args:
            if arg not in conf:
                raise MissingArgumentException(arg)

        # Define default values for no defined arguments
        for args, value in self.arguments.items():
            is_precised = False
            for name in value.names:
                if name in conf:
                    is_precised = True
                    break
            if not is_precised and value.default_value is not None:
                conf[args] = value.default_value

        return conf

class SubgroupParserGroup:
    """"""
    def __init__(self, group_name: str, help_text: str=''):
        self.group_name = group_name
        self.help_text = help_text
        self.subparsers = {}

    def contains(self, name: str):
        """"""
        return name in self.subparsers

    def add_subgroup_parser(self, name: str, subparser: BaseConfigParser):
        """"""
        self.subparsers[name] = subparser

    def get_subgroup_parser(self, name: str)->BaseConfigParser:
        """"""
        return self.subparsers[name]

    def __iter__(self):
        return iter(self.subparsers.items())

    def get_help(self):
        """
        return help string
        """
        s = self.group_name + ' details :\n'
        for subparser_name, subparser in self.subparsers.items():
            s += '  --' + self.group_name + ' ' + subparser_name + ':\n'
            s += subparser.get_help()
            s += '\n'

        return s

class SubgroupConfigParser(BaseConfigParser):
    """"""
    def __init__(self, name: str):
        BaseConfigParser.__init__(self)
        self.name = name

    def _unknown_argument_behaviour(self, arg_name: str, val: Any, args: list,
                                    acc: dict):
        return args, acc

    def parse(self, token_list: list)->(list, dict):
        """
        Parse the given token list until an unknown argument is caught

        :param list token_list: the token list currently parsed

        :result: the current result of the parser

        :return (list, dict): a tuple containing the token list without the
                              parsed argument and the result of the parsing

        """
        local_result = deepcopy(self.default_values)
        if not token_list:
            return token_list, local_result

        return self._parse(token_list, local_result)

    def get_help(self)-> str:
        """
        return help string
        """
        return self._get_arguments_str('    ')


class RootConfigParser(BaseConfigParser):
    """"""
    def __init__(self, help_arg: bool=True):
        """
        :param bool help_arg: if True, add a -h/--help argument that display help
        """
        BaseConfigParser.__init__(self)
        self.short_arg = ''
        self.long_arg = []
        self.subgroup_parsers = {}

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

    def parse(self, args: str)-> dict:
        """
        :param str args: string that contains the arguments and their values

        :return dict:

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
        args = list(map(lambda x: (extract_minus(x[0]), x[1]), args))

        # verify if help argument exists in args

        if self.help_arg:
            for arg_name, _ in args:
                if arg_name in ('h', 'help'):
                    print(self.get_help())
                    sys.exit(0)

        acc = deepcopy(self.default_values)

        args, acc = self._parse(args, acc)

        return acc

    def _unknown_argument_behaviour(self, arg_name: str, val: Any, args: list,
                                    acc: dict):
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
            raise TooManyArgumentNamesException(names[1])

        def gen_name(name):
            if len(name) == 1:
                return name + ('' if is_flag else ':')
            return name + ('' if is_flag else '=')

        for name in names:
            if len(name) == 1:
                self.short_arg += gen_name(name)
            else:
                self.long_arg.append(gen_name(name))

    def add_argument(self, *names, is_flag: bool =False, action: Callable=store_val, default_value: Any=None,
                     help_text: str='', argument_type:type =str, is_mandatory:bool = False):
        BaseConfigParser.add_argument(self, *names, is_flag=is_flag, action=action, default_value=default_value,
                                      help_text=help_text, argument_type=argument_type, is_mandatory=is_mandatory)
        self._add_argument_names(names, is_flag)

    def add_subgroup_parser(self, subgroup_type: str, subgroup_parser: SubgroupConfigParser, help_text: str= ''):
        """
        Add a subparser that will be used by the argument *group_name*
        The group must contain a name action
        :param str subgroup_type: the group type
        :param SubgroupConfigParser subgroup_parser: The subgroup parser
        :param str help_text: help text related to the parser

        :raise AlreadyAddedArgumentException: when attempting to add an
                                              argument that already have been
                                              added to this parser
        """
        def _action(arg: str, val: Any, args: list, acc: dict):
            if arg not in acc:
                acc[arg] = {}

            parser = self.subgroup_parsers[arg].get_subgroup_parser(val)
            args, parse_result = parser.parse(args)

            if 'name' not in parse_result:
                raise NoNameSpecifiedForGroupException(subgroup_type)

            subgroup_name = parse_result['name']
            del parse_result['name']

            if subgroup_name in acc[arg]:
                raise SubgroupAlreadyExistException(subgroup_name)

            acc[arg][subgroup_name] = parse_result
            acc[arg][subgroup_name]['type'] = parser.name

            return args, acc

        if 'name' not in subgroup_parser.arguments:
            raise SubgroupParserWithoutNameArgumentException()
        if subgroup_type not in self.subgroup_parsers:
            self.subgroup_parsers[subgroup_type] = SubgroupParserGroup(subgroup_type, help_text=help_text)
            self.add_argument(subgroup_type, action=_action, help_text=help_text)
        else:
            if self.subgroup_parsers[subgroup_type].contains(subgroup_parser.name):
                raise AlreadyAddedArgumentException(subgroup_parser.name)

        self.subgroup_parsers[subgroup_type].add_subgroup_parser(subgroup_parser.name, subgroup_parser)

        for action_name, action in subgroup_parser.arguments.items():
            self._add_argument_names([action_name], action.is_flag)


def cast_argument_value(arg_name: str, val: Any, argument: ConfigurationArgument):
    if not argument.is_flag:
        try:
            return argument.type(val)
        except ValueError as exn:
            raise BadTypeException(arg_name, argument.type) from exn
    return val