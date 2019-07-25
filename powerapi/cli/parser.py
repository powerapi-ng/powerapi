# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
from copy import deepcopy

from powerapi.exception import PowerAPIException


def _extract_minus(arg):
    if len(arg) > 2:
        return arg[2:]
    return arg[1]


def _cast_argument_value(arg_name, val, action):
    if not action.is_flag:
        try:
            return action.type(val)
        except ValueError:
            raise BadTypeException(arg_name, action.type)
    return val


def _find_longest_name(names):
    max_len = 0
    longest_name = ''
    for name in names:
        if len(name) > max_len:
            longest_name = name
            max_len = len(name)
    return longest_name


#############
# EXCEPTION #
#############
class ParserException(PowerAPIException):
    def __init__(self, argument_name):
        super().__init__()
        self.argument_name = argument_name


class NoNameSpecifiedForComponentException(ParserException):
    """
    Exception raised when attempting to parse substring thant describe a component which not contains the component name
    """


class ComponentAlreadyExistException(ParserException):
    """
    Exception raised when attempting to parse a substring to create a component with a name that already exist
    """


class BadValueException(ParserException):
    """
    Exception raised when attempting to parse a value that doens't respect the
    check function of its argument
    """
    def __init__(self, argument_name, msg):
        ParserException.__init__(self, argument_name)
        self.msg = msg


class SubParserWithoutNameArgumentException(PowerAPIException):
    """
    Exception raised when a subparser without argument name is added to a parser
    """


class TooManyArgumentNamesException(ParserException):
    """
    Exception raised when attemtping to add an argument with too much names

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)


class AlreadyAddedArgumentException(ParserException):
    """
    Exception raised when attempting to add an argument to a parser that already
    have this argument

    """
    def __init__(self, argument_name):
        super().__init__(argument_name)
        self.msg = 'Parser already contain an argument ' + argument_name


class MissingValueException(ParserException):
    """
    Exception raised when an argument that require a value is caught without
    its value

    """
    def __init__(self, argument_name):
        super().__init__(argument_name)
        self.msg = 'Argument ' + argument_name + ' require a value'


class UnknowArgException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle

    """
    def __init__(self, argument_name):
        super().__init__(argument_name)
        self.msg = 'Unknow argument ' + argument_name


class BadTypeException(ParserException):
    """
    Exception raised when an argument is parsed with a value of an incorrect
    type

    """
    def __init__(self, argument_name, type):
        super().__init__(argument_name)
        self.type_name = type.__name__
        self.article = 'an' if self.type_name in ('a', 'e', 'i', 'o', 'u', 'y') else 'a'


class BadContextException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle in
    the current context
    """
    def __init__(self, argument_name, context_list):
        super().__init__(argument_name)
        self.context_list = context_list
        self.msg = 'argument ' + argument_name + 'not used in the correct context\nUse it with the following arguments :'
        for main_arg_name, context_name in context_list:
            self.msg += '\n  --' + main_arg_name + ' ' + context_name


#################
# ACTION LAMBDA #
#################
def store_val(arg, val, args, acc):
    """
    lambda that store the value of the argument on the parser result

    """
    if val == '':
        val = None

    acc[arg] = val
    return args, acc


def store_true(arg, _, args, acc):
    """
    lambda that store a True boolean value on the parser result

    """
    acc[arg] = True
    return args, acc


class ParserAction:
    """
    Action binded to an argument
    """
    def __init__(self, name_list, is_flag, action, default_value, check_fun,
                 check_msg, help_str, type):
        self.name_list = name_list
        self.is_flag = is_flag
        self.action = action
        self.default_value = default_value
        self.check_fun = check_fun
        self.check_msg = check_msg
        self.help_str = help_str
        self.type = type


class SubParserGroup:

    def __init__(self, group_name, help_str=''):
        self.group_name = group_name
        self.help_str = help_str
        self.subparsers = {}

    def contains(self, name):
        return name in self.subparsers

    def add_subparser(self, name, subparser):
        self.subparsers[name] = subparser

    def get_subparser(self, name):
        return self.subparsers[name]

    def __iter__(self):
        return iter(self.subparsers.items())

    def get_help(self):
        s = self.group_name + ' details :\n'
        for subparser_name, subparser in self.subparsers.items():
            s += '  --' + self.group_name + ' ' + subparser_name + ':\n'
            s += subparser.get_help()
            s += '\n'

        return s


class Parser:

    def __init__(self):
        self.actions = {}
        self.default_values = {}
        self.action_list = []

    def add_argument(self, *names, flag=False, action=store_val, default=None,
                     check=None, check_msg='', help='', type=str):
        """add an optional argument to the parser that will activate an action

        :param str *names: names of the optional argument that will be bind to
                           the action (could be long or short name)

        :param bool flag: True if the argument doesn't require to be followed
                           by a value

        :param lambda action: action that will be executed when the argument is
                              caught by the parser. the lambda take 4 parameters
                              (the name of the argument caught by the parser,
                              the value attached to this arguemnt, the current
                              list of arguments that is parsed by the parser and
                              the parser result) and return a list of token and
                              a parser result(dict)

        :param default: the default value attached to this argument

        :param lambda check: function that is called to validate the value
                             required by the argument this function take one
                             parameter (the value) and return a boolean

        :param str check msg: message displayed when the caught value doesn't
                              respect the check function

        :param str help: string that describe the argument

        :param type type: type of the value that the argument must catch

        :raise AlreadyAddedArgumentException: when attempting to add an
                                               argument that already have been
                                               added to this parser

        """
        parser_action = ParserAction(list(names), flag, action, default, check,
                                     check_msg, help, type)

        for name in names:
            if name in self.actions:
                raise AlreadyAddedArgumentException(name)
            self.actions[name] = parser_action

        action_name = _find_longest_name(names)

        if default is not None:
            self.default_values[action_name] = default

        self.action_list.append(parser_action)

    def _get_action_list_str(self, indent):
        s = ''
        for action in self.action_list:
            s += indent + ', '.join(map(lambda x: '-' + x if len(x) == 1 else '--' + x, action.name_list))
            s += ' : ' + action.help_str + '\n'
        return s

    def _unknow_argument_behaviour(self, arg, val, args, acc):
        raise NotImplementedError()

    def _parse(self, args, acc):
        while args != []:
            arg, val = args.pop(0)

            if arg not in self.actions:
                args.insert(0, (arg, val))
                return self._unknow_argument_behaviour(arg, val, args, acc)

            action = self.actions[arg]

            arg_long_name = _find_longest_name(action.name_list)
            val = _cast_argument_value(arg_long_name, val, action)

            # check value
            if action.check_fun is not None and not action.check_fun(val):
                raise BadValueException(arg_long_name, action.check_msg)
            args, acc = action.action(arg_long_name, val, args, acc)

        return args, acc


class ComponentSubParser(Parser):

    def __init__(self, name):
        Parser.__init__(self)
        self.name = name

    def _unknow_argument_behaviour(self, arg, val, args, acc):
        return args, acc

    def subparse(self, token_list):
        """
        Parse the given token list until an unknow argument is caught

        :param list token_list: the token list currently parsed

        :result: the current result of the parser

        :return (list, dict): a tuple containing the token list without the
                              parsed argument and the result of the parsing

        """
        local_result = deepcopy(self.default_values)
        if token_list == []:
            return token_list, local_result

        return self._parse(token_list, local_result)


    def get_help(self):
        return self._get_action_list_str('    ')


class MainParser(Parser):

    def __init__(self, help_arg=True):
        """
        :param bool help_arg: if True, add a -h/--help argument that display help
        """
        Parser.__init__(self)
        self.short_arg = ''
        self.long_arg = []
        self.subparsers_group = {}

        self.help_arg = help_arg
        if help_arg:
            self.add_argument('h', 'help', flag=True, action=None)

    def parse(self, args):
        """
        :param str args: string that contains the arguments and their values

        :return dict:

        :raise UnknowArgException: when the parser catch catch an argument that
                                   this parser can't handle

        :raise BadContextException: when an argument that the parser can't
                                    handle in the current context is caught

        :raise MissingValueException: when an argument that require a value is
                                      caught without its value

        :raise BadTypeException: when an argument is parsed with a value of an
                                 incorrect type

        :raise BadValueException: when a value that doens't respect the check
                                  function of its argument is parsed

        """
        try:
            args, _ = getopt.getopt(args, self.short_arg, self.long_arg)
        except getopt.GetoptError as exn:
            if 'recognized' in exn.msg:
                raise UnknowArgException(exn.opt)
            elif 'requires' in exn.msg:
                raise MissingValueException(exn.opt)

        # retirer les moins
        args = list(map(lambda x: (_extract_minus(x[0]), x[1]), args))

        # verify if help argument exists in args
        if self.help_arg:
            for arg_name, _ in args:
                if arg_name in ('h', 'help'):
                    print(self.get_help())
                    exit(0)

        acc = deepcopy(self.default_values)

        args, acc = self._parse(args, acc)
        return acc

    def get_help(self):
        s = 'main arguments:\n'
        s += self._get_action_list_str('  ')
        s += '\n'

        for _, subparser_group in self.subparsers_group.items():
            s += subparser_group.get_help()

        return s

    def _unknow_argument_behaviour(self, arg_name, val, args, acc):
        good_contexts = []
        for main_arg_name, subparser_group in self.subparsers_group.items():
            for subparser_name, subparser in subparser_group:
                if arg_name in subparser.actions:
                    good_contexts.append((main_arg_name, subparser_name))
        raise BadContextException(arg_name, good_contexts)

    def _add_argument_names(self, names, is_flag):

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

    def add_argument(self, *names, flag=False, action=store_val, default=None,
                     check=None, help='', type=str):
        Parser.add_argument(self, *names, flag=flag, action=action,
                            default=default, check=check, help=help,
                            type=type)
        self._add_argument_names(names, flag)

    def add_formula_subparser(self, component_type, subparser, help_str=''):
        """
        Add a subparser that will be used by the argument *component_name*

        :param str component_type:
        :param ComponentSubParser subparser:

        :raise AlreadyAddedArgumentException: when attempting to add an
                                              argument that already have been
                                              added to this parser
        """
        def _action(arg, val, args, acc):
            if arg not in acc:
                acc[arg] = {}

            subparser = self.subparsers_group[arg].get_subparser(val)
            args, subparse_result = subparser.subparse(args)

            acc[arg][subparser.name] = subparse_result
            return args, acc

        if component_type not in self.subparsers_group:
            self.subparsers_group[component_type] = SubParserGroup(component_type, help_str=help_str)
            self.add_argument(component_type, action=_action, help=help_str)
        else:
            if self.subparsers_group[component_type].contains(subparser.name):
                raise AlreadyAddedArgumentException(subparser.name)

        self.subparsers_group[component_type].add_subparser(subparser.name, subparser)

        for action_name, action in subparser.actions.items():
            self._add_argument_names([action_name], action.is_flag)


    def add_component_subparser(self, component_type, subparser, help_str=''):
        """
        Add a subparser that will be used by the argument *component_name*

        :param str component_type:
        :param ComponentSubParser subparser:

        :raise AlreadyAddedArgumentException: when attempting to add an
                                              argument that already have been
                                              added to this parser
        """
        def _action(arg, val, args, acc):
            if arg not in acc:
                acc[arg] = {}

            subparser = self.subparsers_group[arg].get_subparser(val)
            args, subparse_result = subparser.subparse(args)

            if 'name' not in subparse_result:
                raise NoNameSpecifiedForComponentException(component_type)

            component_name = subparse_result['name']

            if subparser.name not in acc[arg]:
                acc[arg][subparser.name] = {}

            if component_name in acc[arg][subparser.name]:
                raise ComponentAlreadyExistException(component_name)

            acc[arg][subparser.name][component_name] = subparse_result
            return args, acc

        if 'name' not in subparser.actions:
            raise SubParserWithoutNameArgumentException()
        if component_type not in self.subparsers_group:
            self.subparsers_group[component_type] = SubParserGroup(component_type, help_str=help_str)
            self.add_argument(component_type, action=_action, help=help_str)
        else:
            if self.subparsers_group[component_type].contains(subparser.name):
                raise AlreadyAddedArgumentException(subparser.name)

        self.subparsers_group[component_type].add_subparser(subparser.name, subparser)

        for action_name, action in subparser.actions.items():
            self._add_argument_names([action_name], action.is_flag)
