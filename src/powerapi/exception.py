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
        Exception.__init__(self, *args)


class PowerAPIExceptionWithMessage(PowerAPIException):
    """
    PowerAPIException base class
    """

    def __init__(self, msg):
        PowerAPIException.__init__(self, msg)
        self.msg = msg


class ConfigurationError(PowerAPIExceptionWithMessage):
    """
    Exception raised when configuration loading or validation fails.
    """

    def __init__(self, reason: str, path: str | None = None):
        """
        Initialize a configuration error.
        :param reason: User-facing explanation of the invalid configuration.
        :param path: Dotted path of the invalid value, or None for an error affecting the full configuration.
        """
        self.reason = reason
        self.path = path
        prefix = f'Invalid configuration at "{path}": ' if path else 'Invalid configuration: '
        super().__init__(prefix + reason)


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
