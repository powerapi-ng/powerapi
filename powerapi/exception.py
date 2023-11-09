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


class ParserException(PowerAPIException):
    """
    Base Exception for parser error
    """

    def __init__(self, argument_name: str):
        PowerAPIException.__init__(self)
        self.argument_name = argument_name


class NoNameSpecifiedForSubgroupException(ParserException):
    """
    Exception raised when attempting to parse substring thant describe a component which not contains the component name
    """


class SubgroupAlreadyExistException(ParserException):
    """
    Exception raised when attempting to parse a substring to create a component with a name that already exist
    """


class SubgroupDoesNotExistException(ParserException):
    """
    Exception raised when attempting to add arguments to a subgroup that does not exist
    """


class SubgroupParserWithoutNameArgumentException(PowerAPIException):
    """
    Exception raised when a subparser without argument name is added to a parser
    """


class TooManyArgumentNamesException(ParserException):
    """
    Exception raised when attemtping to add an argument with too much names

    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)


class AlreadyAddedArgumentException(ParserException):
    """
    Exception raised when attempting to add an argument to a parser that already
    have this argument

    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)
        self.msg = 'Parser already contain an argument ' + argument_name


class AlreadyAddedSubparserException(ParserException):
    """
    Exception raised when attempting to add a parser that already exists    """

    def __init__(self, parser_name: str):
        ParserException.__init__(self, parser_name)
        self.msg = 'Parser already contain SubParser with name ' + parser_name


class AlreadyAddedSubgroupException(ParserException):
    """
    Exception raised when attempting to add a subgroup that already exists    """

    def __init__(self, subgroup_name: str):
        ParserException.__init__(self, subgroup_name)
        self.msg = 'Parser already contain Subgroup with name ' + subgroup_name


class MissingArgumentException(ParserException):
    """
    Exception raised when a mandatory argument is missing
    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument with name(s) ' + argument_name + ' is missing'


class RepeatedArgumentException(ParserException):
    """
    Exception raised when an argument is repeated several times in a configuration
    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument with name(s) ' + argument_name + ' is repeated'


class MissingValueException(ParserException):
    """
    Exception raised when an argument that require a value is caught without
    its value

    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)
        self.msg = 'Argument ' + argument_name + ' require a value'


class UnknownArgException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle

    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)
        self.msg = 'Unknown argument ' + argument_name


class BadTypeException(ParserException):
    """
    Exception raised when an argument is parsed with a value of an incorrect type
    """

    def __init__(self, argument_name: str, arg_type: type):
        ParserException.__init__(self, argument_name)
        self.msg = argument_name + " expect " + arg_type.__name__


class BadContextException(ParserException):
    """
    Exception raised when the parser catch an argument that it can't handle in
    the current context
    """

    def __init__(self, argument_name: str, context_list: list):
        ParserException.__init__(self, argument_name)
        self.context_list = context_list
        self.msg = 'argument ' + argument_name + 'not used in the correct context\nUse it with the following arguments :'
        for main_arg_name, context_name in context_list:
            self.msg += '\n  --' + main_arg_name + ' ' + context_name


class NotAllowedArgumentValueException(PowerAPIException):
    """
    This exception happens when the configuration define an argument value that is incompatible with other arguments'
    values
    """


class FileDoesNotExistException(PowerAPIException):
    """
    This exception happens when the configuration define a input file that does not exist or is not accessible
    """

    def __init__(self, file_name: str):
        PowerAPIException.__init__(self)
        self.file_name = file_name
        self.msg = "The File " + self.file_name + " does not exist or is not accessible"


class SameLengthArgumentNamesException(ParserException):
    """
    Exception raised when attempting to add an argument with names that have the same length

    """

    def __init__(self, argument_name: str):
        ParserException.__init__(self, argument_name)


class ModelNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a model factory with a name already bound to another
    model factory in the DBActorGenerator
    """

    def __init__(self, model_name: str):
        PowerAPIException.__init__(self)
        self.model_name = model_name


class DatabaseNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a database factory with a name that is not bound to
    another database factory in the DBActorGenerator
    """

    def __init__(self, database_name: str):
        PowerAPIException.__init__(self)
        self.database_name = database_name


class DatabaseNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a database factory with a name already bound to
    another database factory in the DBActorGenerator
    """

    def __init__(self, database_name: str):
        PowerAPIException.__init__(self)
        self.database_name = database_name


class ModelNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a model factory with a name that is not bound to
    another model factory in the DBActorGenerator
    """

    def __init__(self, model_name: str):
        PowerAPIException.__init__(self)
        self.model_name = model_name


class InvalidPrefixException(PowerAPIException):
    """
    Exception raised when attempting to add a new prefix that is a prefix of an existing one or
    vice-versa
    """

    def __init__(self, existing_prefix: str, new_prefix: str):
        PowerAPIException.__init__(self)
        self.new_prefix = new_prefix
        self.existing_prefix = existing_prefix
        self.msg = "The new prefix " + self.new_prefix + " has a conflict with the existing prefix " \
                   + self.existing_prefix


class LibvirtException(PowerAPIException):
    """
    Exception raised when there are issues regarding the import of LibvirtException
    """

    def __init__(self, _):
        PowerAPIException.__init__(self)


class ProcessorTypeDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a ProcessorActorGenerator a processor factory with a type that is not
    bound to a processor factory
    """

    def __init__(self, processor_type: str):
        PowerAPIException.__init__(self)
        self.processor_type = processor_type


class ProcessorTypeAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a ProcessorActorGenerator a processor factory with a type already bound
    to another processor factory
    """

    def __init__(self, processor_type: str):
        PowerAPIException.__init__(self)
        self.processor_type = processor_type


class UnsupportedActorTypeException(ParserException):
    """
    Exception raised when the binding manager do not support an actor type
    """

    def __init__(self, actor_type: str):
        ParserException.__init__(self, argument_name=actor_type)
        self.msg = 'Unsupported Actor Type ' + actor_type


class UnknownMessageTypeException(PowerAPIException):
    """
    Exception happen when we don't know the message type
    """


class MonitorTypeDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a MonitorGenerator a monitor factory with a type that is not
    bound to a monitor factory
    """

    def __init__(self, monitor_type: str):
        PowerAPIException.__init__(self)
        self.monitor_type = monitor_type


class UnexistingActorException(PowerAPIException):
    """
    Exception raised when an actor referenced in a processor does not exist
    """

    def __init__(self, actor: str):
        PowerAPIException.__init__(self)
        self.actor = actor


class BindingWrongActorsException(PowerAPIException):
    """
    Exception raised when at least one of the actors in a binding is not of a given type
    """

    def __init__(self):
        PowerAPIException.__init__(self)


class TargetActorAlreadyUsed(PowerAPIException):
    """
    Exception raised when an actor is used by more than one processor
    """

    def __init__(self, target_actor: str):
        PowerAPIException.__init__(self)
        self.target_actor = target_actor
