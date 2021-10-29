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

from typing import Dict, Type
from powerapi.cli.parser import MainParser, ComponentSubParser

from powerapi.cli.parser import MissingValueException
from powerapi.cli.parser import BadTypeException, BadContextException, MissingArgumentException
from powerapi.cli.parser import UnknowArgException, AlreadyAddedArgumentException, AlreadyAddedSubparserException
from powerapi.cli.parser import store_val
from powerapi.cli.parser import _find_longest_name


def extract_file_names(arg, val, args, acc):
    """
    action used to convert string from --files parameter into a list of file name
    """
    acc[arg] = val.split(',')
    return args, acc


class ConfigParserArg:
    """
    Parser abstraction that retrieve the config.
    """
    def __init__(self, name_list: list, is_flag: bool, default_value, help: str, type: Type, mandatory: bool):
        self.names = name_list
        self.is_flag = is_flag
        self.default_value = default_value
        self.help = help
        self.type = type
        self.is_mandatory = mandatory


class ConfigParser:
    """ The config parser call the right parser on the CLI or the config file and then verify the type and add the default id needed."""
    def __init__(self):
        self.cli_parser = None
        self.args = {}

    def _get_mandatory_args(self):
        """
        Return the list of mandatory arguments
        """
        mand_arg = []
        for name, value in self.args.items():
            if value.is_mandatory:
                mand_arg.append(name)
        return mand_arg

    def add_argument(self, *names, flag=False, action=store_val, default=None,
                     help='', type=str, mandatory=False):
        """
        Add an argument to the parser and its specification
        """
        parser_val = ConfigParserArg(list(names), flag, default, help, type, mandatory)

        name = _find_longest_name(names)
        if name in self.args:
            raise AlreadyAddedArgumentException(name)
        self.args[name] = parser_val
        self.cli_parser.add_argument(*names, flag=flag, action=action, default=default, help=help, type=type)


class SubConfigParser(ConfigParser):
    """
    Sub Parser for MainConfigParser
    """
    def __init__(self, name: str):
        ConfigParser.__init__(self)
        self.subparser = {}
        self.cli_parser = ComponentSubParser(name)
        self.name = name

    def validate(self, conf: Dict):
        """ Check the parsed configuration"""

        # Check that all the mandatory arguments are precised
        mandatory_args = self._get_mandatory_args()
        for arg in mandatory_args:
            if arg not in conf:
                raise MissingArgumentException(arg)

        # check types
        for args, value in conf.items():
            for _, waited_value in self.args.items():
                if args in waited_value.names:
                    # check type
                    if not isinstance(value, waited_value.type) and not waited_value.is_flag:
                        raise BadTypeException(args, waited_value.type)

        for args, value in self.args.items():
            is_precised = False
            for name in value.names:
                if name in conf:
                    is_precised = True
                    break
            if not is_precised and value.default_value is not None:
                conf[args] = value.default_value

        return conf


class MainConfigParser(ConfigParser):
    """
    Parser abstraction for the configuration
    """
    def __init__(self):
        ConfigParser.__init__(self)
        self.subparser = {}
        self.cli_parser = MainParser()

    def add_subparser(self, name, subparser: SubConfigParser, help=''):

        """
        Add a SubParser to call when <name> is encoutered
        When name is encoutered, the subarpser such as subparser.name match conf[name].type

        """
        if name in self.subparser:
            if subparser.name in list(self.subparser[name]):
                raise AlreadyAddedSubparserException(name)
        else:
            self.subparser[name] = {}

        self.subparser[name][subparser.name] = subparser

        self.cli_parser.add_actor_subparser(name, subparser.cli_parser, help)

    def _parse_cli(self, cli_line):
        return self.cli_parser.parse(cli_line)

    @staticmethod
    def _parse_file(filename):
        config_file = open(filename, 'r')
        conf = json.load(config_file)
        return conf

    def _validate(self, conf: Dict):
        """ Check the parsed configuration"""

        # Check that all the mandatory arguments are precised
        mandatory_args = self._get_mandatory_args()
        for arg in mandatory_args:
            if arg not in conf:
                raise MissingArgumentException(arg)

        # check types
        for args, value in conf.items():
            is_an_arg = False
            if args in self.subparser:
                for _, dic_value in value.items():
                    self.subparser[args][dic_value["type"]].validate(dic_value)
                    is_an_arg = True

            for _, waited_value in self.args.items():
                if args in waited_value.names:
                    is_an_arg = True
                    # check type
                    if not isinstance(value, waited_value.type) and not waited_value.is_flag:
                        raise BadTypeException(args, waited_value.type)

            if not is_an_arg:
                raise UnknowArgException(args)

        for args, value in self.args.items():
            is_precised = False
            for name in value.names:
                if name in conf:
                    is_precised = True
                    break
            if not is_precised and value.default_value is not None:
                conf[args] = value.default_value

        return conf

    def parse(self, args=None):
        """
        Find the configuration method (CLI or config file)
        Call the method to produce a configuration dictionnary
        check the configuration
        """

        if args is None:
            args = sys.argv
        i = 0
        filename = None
        for s in args:
            if s == '--config-file':
                if i + 1 == len(args):
                    logging.error("CLI Error: config file path needed with argument --config-file")
                    sys.exit(-1)
                filename = args[i + 1]
            i += 1

        try:
            if filename is not None:
                conf = self._parse_file(filename)
            else:
                conf = self._parse_cli(args[1:])
            conf = self._validate(conf)

        except MissingValueException as exn:
            msg = 'CLI error: argument ' + exn.argument_name + ': expect a value'
            logging.error(msg)
            sys.exit(-1)

        except BadTypeException as exn:
            msg = "Configuration error: " + exn.msg
            logging.error(msg)
            sys.exit(-1)

        except UnknowArgException as exn:
            msg = 'Configuration error: unknow argument ' + exn.argument_name
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
            logging.error('Configuration Error: JSON Error: ' + exn.msg + ' at line' + exn.lineno + ' colomn ' + exn.colno)
            sys.exit(-1)

        except MissingArgumentException as exn:
            logging.error("Configuration Error: " + exn.msg)
            sys.exit(-1)

        return conf
