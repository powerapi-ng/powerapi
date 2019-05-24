"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import getopt
from copy import deepcopy


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


#############
# EXCEPTION #
#############
class ParserException(Exception):
    def __init__(self, argument_name):
        Exception.__init__(self)
        self.argument_name = argument_name


class AlreadyAddedArgumentException(ParserException):
    """
    Exception raised when attempting to add an argument to a parser that already
    have this argument

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Parser already contain an argument ' + argument_name


class MissingValueException(ParserException):
    """
    Exception raised when an argument that require a value is caught without
    its value

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument ' + argument_name + ' require a value'


class UnknowArgException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Unknow argument ' + argument_name


class BadTypeException(ParserException):
    """
    Exception raised when an argument is parsed with a value of an incorrect
    type

    """
    def __init__(self, argument_name, type):
        ParserException.__init__(self, argument_name)
        self.context_name = type
        self.msg = 'argument ' + argument_name + 'can\'t been casted to ' + type.__name__


class BadContextException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle in
    the current context
    """
    def __init__(self, argument_name, context_list):
        ParserException.__init__(self, argument_name)
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


def store_true(arg, val, args, acc):
    """
    lambda that store a True boolean value on the parser result

    """
    acc[arg] = True
    return args, acc


class ParserAction:
    """
    Action binded to an argument
    """
    def __init__(self, name_list, is_flag, action, default_value, check_val,
                 help_str, type):
        self.name_list = name_list
        self.is_flag = is_flag
        self.action = action
        self.default_value = default_value
        self.check_val = check_val
        self.help_str = help_str
        self.type = type


class Parser:

    def __init__(self):
        self.actions = {}
        self.default_values = {}

    def add_argument(self, *names, flag=False, action=store_val, default=None,
                     check=None, help='', type=str):
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

        :param str help: string that describe the argument

        :param type type: type of the value that the argument must catch

        :raise AlreadyAddedArgumentException: when attempting to add an
                                               argument that already have been
                                               added to this parser

        """
        parser_action = ParserAction(list(names), flag, action, default, check,
                                     help, type)

        for name in names:
            if default is not None:
                self.default_values[name] = default

            if name in self.actions:
                raise AlreadyAddedArgumentException(name)
            self.actions[name] = parser_action

    def _unknow_argument_behaviour(self, arg, val, args, acc):
        raise NotImplementedError()

    def _parse(self, args, acc):
        while args != []:
            arg, val = args.pop(0)

            if arg not in self.actions:
                args.insert(0, (arg, val))
                return self._unknow_argument_behaviour(arg, val, args, acc)

            action = self.actions[arg]

            val = _cast_argument_value(arg, val, action)
            args, acc = action.action(arg, val, args, acc)

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

        local_result['type'] = self.name

        return self._parse(token_list, local_result)


class MainParser(Parser):

    def __init__(self):
        Parser.__init__(self)
        self.short_arg = ''
        self.long_arg = []
        self.subparsers_group = {}

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

        """
        try:
            args, _ = getopt.getopt(args, self.short_arg, self.long_arg)
        except getopt.GetoptError as exn:
            if 'recognized' in exn.msg:
                raise UnknowArgException(exn.opt[:1])
            elif 'requires' in exn.msg:
                raise MissingValueException(exn.opt[:1])

        # retirer les moins
        args = list(map(lambda x: (_extract_minus(x[0]), x[1]), args))

        acc = deepcopy(self.default_values)

        args, acc = self._parse(args, acc)
        return acc

    def _unknow_argument_behaviour(self, arg_name, val, args, acc):
        good_contexts = []
        for main_arg_name, subparser_group in self.subparsers_group.items():
            for subparser_name, subparser in subparser_group.items():
                if arg_name in subparser.actions:
                    good_contexts.append((main_arg_name, subparser_name))
        raise BadContextException(arg_name, good_contexts)

    def _add_argument_names(self, names, is_flag):
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

    def add_component_subparser(self, component_name, subparser):
        """
        Add a subparser that will be used by the argument *component_name*

        :param str component_name:
        :param ComponentSubParser subparser:

        :raise AlreadyAddedArgumentException: when attempting to add an
                                              argument that already have been
                                              added to this parser
        """
        def _action(arg, val, args, acc):
            if arg not in acc:
                acc[arg] = []

            subparser = self.subparsers_group[arg][val]
            args, subparse_result = subparser.subparse(args)
            acc[arg].append(subparse_result)
            return args, acc

        if component_name not in self.subparsers_group:
            self.subparsers_group[component_name] = {}
            self.add_argument(component_name, action=_action)
        else:
            if subparser.name in self.subparsers_group[component_name]:
                raise AlreadyAddedArgumentException(subparser.name)

        self.subparsers_group[component_name][subparser.name] = subparser

        for action_name, action in subparser.actions.items():
            self._add_argument_names(action_name, action.is_flag)
