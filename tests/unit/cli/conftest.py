# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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
import os

import pytest
import tests.utils.cli as test_files_module
from powerapi.cli.config_parser import SubgroupConfigParser, BaseConfigParser, store_true, RootConfigParser
from powerapi.cli.parsing_manager import RootConfigParsingManager


@pytest.fixture(name="invalid_csv_io_stream_config")
def csv_io_stream_config():
    """
     Invalid configuration with csv as input and output and stream mode enabled
    """
    return {
        "verbose": True,
        "stream": True,
        "input": {
            "puller": {
                "model": "HWPCReport",
                "type": "csv",
                "files": "/tmp/rapl.csv,/tmp/msr.csv"
            }
        },
        "output": {
            "pusher_power": {
                "type": "csv",
                "model": "PowerReport",
                "directory": "/tmp/formula_results"

            }
        },
    }


@pytest.fixture
def csv_io_postmortem_config(invalid_csv_io_stream_config):
    """
     Valid configuration with csv as input and output and stream mode disabled
    """
    invalid_csv_io_stream_config["stream"] = False
    return invalid_csv_io_stream_config


@pytest.fixture()
def subgroup_parser():
    """
    A subgroup parser with one argument "-a"
    """
    parser = SubgroupConfigParser('test')
    parser.add_argument('a', is_flag=True)
    return parser


@pytest.fixture
def create_empty_files_from_config(invalid_csv_io_stream_config: dict):
    """
    Create on the module path the files that are indicated on csv input.
    When they are no longer required, those files are erased
    """
    for _, input_config in invalid_csv_io_stream_config['input'].items():
        if input_config['type'] == 'csv':
            list_of_files = input_config['files'].split(",")
            for file_str in list_of_files:
                if os.path.isfile(file_str) is False:
                    with open(file_str, 'w') as file:
                        file.close()

    yield

    for _, input_config in invalid_csv_io_stream_config['input'].items():
        if input_config['type'] == 'csv':
            list_of_files = input_config['files']
            for file_str in list_of_files:
                if os.path.isfile(file_str):
                    os.remove(file_str)


@pytest.fixture
def base_config_parser():
    """
    Return a BaseConfigParser with mandatory and optional arguments
    """

    parser = BaseConfigParser()

    parser.add_argument('arg1', 'argument1', 'argumento1', default_value=3, argument_type=int, is_mandatory=False)

    parser.add_argument('argumento2', 'arg2', argument_type=str, is_mandatory=True)

    parser.add_argument('arg3', 'argument3', argument_type=bool, is_mandatory=False)

    parser.add_argument('dded', 'arg4', argument_type=float, is_mandatory=True)

    parser.add_argument('arg5', '5', default_value='default value', argument_type=str, help_text='help 5')

    return parser


@pytest.fixture
def root_config_parser_with_mandatory_and_optional_arguments():
    """
    Return a RootConfigParser with mandatory and optional arguments
    """

    parser = RootConfigParser()

    parser.add_argument('a', argument_type=bool, is_flag=True, action=store_true)

    parser.add_argument('1', 'argument1', default_value=3, argument_type=int, is_mandatory=False)

    parser.add_argument('argumento2', '2', argument_type=str, is_mandatory=True)

    parser.add_argument('arg3', 'argument3', argument_type=bool, is_mandatory=False)

    parser.add_argument('d', 'arg4', argument_type=float, is_mandatory=True)

    parser.add_argument('arg5', '5', default_value='default value', argument_type=str,
                        help_text='help 5')

    return parser


@pytest.fixture
def base_config_parser_no_mandatory_arguments():
    """
    Return a BaseConfigParser without mandatory arguments
    """
    parser = BaseConfigParser()

    parser.add_argument('arg1', default_value=4, argument_type=int)

    parser.add_argument('arg2', argument_type=str)

    parser.add_argument('arg3', argument_type=bool)

    parser.add_argument('arg4', argument_type=int)

    parser.add_argument('arg5', argument_type=int)

    return parser


@pytest.fixture
def base_config_parser_str_representation():
    """
    Return expected representation for a BaseConfigParser used in unit tests
    """
    return ' --arg1, --argument1, --argumento1 : \n' + \
        ' --argumento2, --arg2 : \n' + \
        ' --arg3, --argument3 : \n' + \
        ' --dded, --arg4 : \n' + \
        ' --arg5, -5 : help 5\n'


@pytest.fixture
def root_config_parsing_manager():
    """
    Return a RootConfigParsingManager with a flag argument 'a'
    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a', argument_type=bool, is_flag=True, action=store_true)

    return parser_manager


@pytest.fixture
def root_config_parsing_manager_with_mandatory_and_optional_arguments():
    """
    Return a RootConfigParsingManager with several arguments, some of them are mandatory
    """
    parser_manager = RootConfigParsingManager()

    parser_manager.add_argument_to_cli_parser('a', argument_type=bool, is_flag=True, action=store_true)

    parser_manager.add_argument_to_cli_parser('1', 'argument1', default_value=3, argument_type=int, is_mandatory=False)

    parser_manager.add_argument_to_cli_parser('argumento2', '2', argument_type=str, is_mandatory=True)

    parser_manager.add_argument_to_cli_parser('arg3', 'argument3', argument_type=bool, is_mandatory=False)

    parser_manager.add_argument_to_cli_parser('d', 'arg4', argument_type=float, is_mandatory=True)

    parser_manager.add_argument_to_cli_parser('arg5', '5', default_value='default value', argument_type=str, help_text='help 5')
    return parser_manager


@pytest.fixture
def test_files_path():
    return test_files_module.__path__[0]
