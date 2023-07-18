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
import json
import logging

from typing import Callable, Any
from powerapi.cli.config_parser import RootConfigParser, SubgroupConfigParser, store_val
from powerapi.exception import MissingArgumentException, BadTypeException, \
    AlreadyAddedSubparserException, UnknownArgException, MissingValueException, BadContextException, \
    RepeatedArgumentException, AlreadyAddedSubgroupException
from powerapi.utils.cli import merge_dictionaries


class BaseConfigParsingManager:
    """ Abstract class for dealing with parsing of configurations. """

    def __init__(self):
        self.cli_parser = None

    def add_argument(self, *names, is_flag: bool = False, action: Callable = store_val,
                     default_value: Any = None, help_text: str = '', argument_type: type = str,
                     is_mandatory: bool = False):
        """
        Add an argument to the parser and its specification

        """
        self.cli_parser.add_argument(*names, is_flag=is_flag, action=action, default_value=default_value,
                                     help_text=help_text, argument_type=bool if is_flag else argument_type,
                                     is_mandatory=is_mandatory)

    def validate(self, conf: dict) -> dict:
        """ Check the parsed configuration"""
        raise NotImplementedError


class SubgroupConfigParsingManager(BaseConfigParsingManager):
    """
    Sub Parser for MainConfigParser
    """

    def __init__(self, name: str):
        BaseConfigParsingManager.__init__(self)
        self.subparser = {}
        self.cli_parser = SubgroupConfigParser(name)
        self.name = name

    def validate(self, conf: dict) -> dict:
        """ Check the parsed configuration"""

        # check types
        for args, value in conf.items():
            for _, waited_value in self.cli_parser.get_arguments().items():
                if args in waited_value.names:
                    # check type
                    if not isinstance(value, waited_value.type) and not waited_value.is_flag and args != 'files':
                        raise BadTypeException(args, waited_value.type)

        # Check that all the mandatory arguments are present
        conf = self.cli_parser.validate(conf=conf)

        return conf


class RootConfigParsingManager(BaseConfigParsingManager):
    """
    Parser abstraction for the configuration
    """

    def __init__(self):
        BaseConfigParsingManager.__init__(self)
        self.subparser = {}
        self.cli_parser = RootConfigParser()

    def add_argument_prefix(self, argument_prefix: str):
        """
        Add a simple argument prefix to the cli_parser
        :param argument_prefix: a new argument prefix to be added
        """
        self.cli_parser.add_argument_prefix(argument_prefix=argument_prefix)

    def add_subgroup(self, name: str, help_text: str = '', prefix: str = ''):
        """
        Add a group to the cli_parser
        :param name: the group's name
        :param help_text: a help text for the subgroup
        :param prefix: a prefix related to the subgroup
        """
        try:
            self.cli_parser.add_subgroup(subgroup_type=name, help_text=help_text, prefix=prefix)
        except AlreadyAddedSubgroupException as exn:
            msg = "Configuration error: " + exn.msg
            logging.error(msg)
            sys.exit(-1)

    def add_subgroup_parser(self, subgroup_name: str, subgroup_parser: SubgroupConfigParsingManager):

        """
        Add a Subgroup Parser to call when <name> is encountered
        When name is encountered, the subgroup parser such as subgroup_parser.name match conf[name].type

        """
        if subgroup_name in self.subparser:
            if subgroup_parser.name in list(self.subparser[subgroup_name]):
                raise AlreadyAddedSubparserException(subgroup_name)
        else:
            self.subparser[subgroup_name] = {}

        self.subparser[subgroup_name][subgroup_parser.name] = subgroup_parser

        self.cli_parser.add_subgroup_parser(subgroup_type=subgroup_name, subgroup_parser=subgroup_parser.cli_parser)

    def _parse_cli(self, cli_line: list) -> dict:
        return self.cli_parser.parse(cli_line)

    def _parse_config_from_json_file(self, file_name: str, current_conf: dict) -> dict:

        # Select for each argument, le long version name
        conf = self.cli_parser.parse_config_dict(file_name=file_name)

        conf = merge_dictionaries(source=current_conf, destination=conf)

        return conf

    def _parse_config_from_environment_variables(self, current_conf: dict) -> dict:

        conf = self.cli_parser.parse_config_environment_variables()

        conf = merge_dictionaries(source=current_conf, destination=conf)

        return conf

    def validate(self, conf: dict) -> dict:
        """ Check the parsed configuration"""

        # check types
        for current_argument_name, current_argument_value in conf.items():
            is_an_arg = False
            if current_argument_name in self.subparser:
                for _, dic_value in current_argument_value.items():
                    self.subparser[current_argument_name][dic_value["type"]].validate(dic_value)
                    is_an_arg = True

            if not is_an_arg:
                for _, argument_definition in self.cli_parser.get_arguments().items():
                    if current_argument_name in argument_definition.names:
                        is_an_arg = True
                        # check type
                        if not isinstance(current_argument_value,
                                          argument_definition.type) and not argument_definition.is_flag:
                            raise BadTypeException(current_argument_name, argument_definition.type)

            if not is_an_arg:
                raise UnknownArgException(current_argument_name)

        # Check that all the mandatory arguments are present
        conf = self.cli_parser.validate(conf)

        return conf

    def parse(self, args: list = None) -> dict:
        """
        Parse the configurations defined via le CLI, Environment Variables and configuration file.
        The priority of defined values is the following:
        1. CLI
        2. Environment Variables
        3. Configuration File

        Call the method to produce a configuration dictionary
        check the configuration
        """

        if not args:
            args = sys.argv

        current_position = 0
        filename = None
        for current_arg in args:
            if current_arg == '--config-file':
                if current_position + 1 == len(args):
                    logging.error("CLI Error: config file path needed with argument --config-file")
                    sys.exit(-1)
                filename = args[current_position + 1]
                args.pop(current_position + 1)
                args.pop(current_position)
                break
            current_position += 1

        try:

            if len(args) > 1:
                conf = self._parse_cli(args[1:])
            else:
                conf = {}
            conf = self._parse_config_from_environment_variables(current_conf=conf)
            if filename:
                conf = self._parse_config_from_json_file(file_name=filename, current_conf=conf)

            # We validate the conf
            conf = self.validate(conf)

        except MissingValueException as exn:
            msg = 'CLI error: argument ' + exn.argument_name + ': expect a value'
            logging.error(msg)
            sys.exit(-1)

        except BadTypeException as exn:
            msg = "Configuration error: " + exn.msg
            logging.error(msg)
            sys.exit(-1)

        except UnknownArgException as exn:
            msg = 'Configuration error: unknown argument ' + exn.argument_name
            logging.error(msg)
            sys.exit(-1)

        except BadContextException as exn:
            msg = 'CLI error: argument ' + exn.argument_name
            msg += ' not used in the correct context\nUse it with the following arguments:'
            for main_arg_name, context_name in exn.context_list:
                msg += '\n  --' + main_arg_name + ' ' + context_name
            logging.error(msg)
            sys.exit(-1)

        except FileNotFoundError:
            logging.error("Configuration Error: configuration file not found")
            sys.exit(-1)

        except json.JSONDecodeError as exn:
            logging.error(
                'Configuration Error: JSON Error: ' + exn.msg + ' at line' + str(exn.lineno) + ' colon ' +
                str(exn.colno))
            sys.exit(-1)

        except MissingArgumentException as exn:
            logging.error("Configuration Error: " + exn.msg)
            sys.exit(-1)

        except RepeatedArgumentException as exn:
            logging.error("Configuration Error: " + exn.msg)
            sys.exit(-1)

        return conf
