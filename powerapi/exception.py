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


class PowerAPIException(Exception):
    """
    PowerAPIException base class
    """
    def __init__(self, *args: object):
        Exception.__init__(self, args)


class PowerAPIExceptionWithMessage(PowerAPIException):
    """
    PowerAPIException base class
    """

    def __init__(self, msg):
        PowerAPIException.__init__(self)
        self.msg = msg


class BadInputData(PowerAPIException):
    """
    Exception raised when the data read in input are not
    in the good format
    """

#############
# EXCEPTION #
#############
class ParserException(PowerAPIException):
    """
    Base Exception for parser error
    """
    def __init__(self, argument_name):
        PowerAPIException.__init__(self)
        self.argument_name = argument_name


class NoNameSpecifiedForComponentException(ParserException):
    """
    Exception raised when attempting to parse substring thant describe a component which not contains the component name
    """


class ComponentAlreadyExistException(ParserException):
    """
    Exception raised when attempting to parse a substring to create a component with a name that already exist
    """


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
        ParserException.__init__(self, argument_name)
        self.msg = 'Parser already contain an argument ' + argument_name


class AlreadyAddedSubparserException(ParserException):
    """
    Exception raised when attempting to add an argument to a parser that already
    have this argument

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Parser already contain SubParser with name ' + argument_name


class MissingArgumentException(ParserException):
    """
    Exception raised when a mandatory argument is missing
    """

    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument ' + argument_name + ' is missing'


class MissingValueException(ParserException):
    """
    Exception raised when an argument that require a value is caught without
    its value

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument ' + argument_name + ' require a value'


class UnknownArgException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle

    """
    def __init__(self, argument_name):
        ParserException.__init__(self, argument_name)
        self.msg = 'Unknow argument ' + argument_name


class BadTypeException(ParserException):
    """
    Exception raised when an argument is parsed with a value of an incorrect type
    """
    def __init__(self, argument_name, arg_type):
        ParserException.__init__(self, argument_name)
        self.msg = argument_name + " expect " + arg_type.__name__


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


