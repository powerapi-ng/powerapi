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

import json

import tests.utils.cli as parent_module


def load_configuration_from_json_file(file_name: str) -> dict:
    """
    Load a json dictionary contained in the given file
    :param str file_name: The file name with extension and without '/' at the begining
    """
    path = parent_module.__path__[0]
    json_file = open(path + '/' + file_name, 'r')
    configuration = json.load(json_file)
    json_file.close()
    return configuration


def generate_configuration_tuples_from_json_file(file_name: str) -> list:
    """
    Generate a list of tuples <argument_name,value> from a dictionary created from a given file
    :param str file_name: The file name with extension and without '/' at the beginning
    """
    arguments = []
    conf = load_configuration_from_json_file(file_name)

    for argument_name, value in conf.items():
        arguments.append((argument_name, value))

    return arguments


def generate_cli_configuration_from_json_file(file_name: str) -> list:
    """
    Generate a list with arguments defined in a json file. The list always has a 'test' string
    as first element followed by --arg1_name, arg1_value, -arg2_name, arg2_value... Each
    argument name has as prefix '-' if it is short (its length == 1) or '--' if it is long (its length>1)
    :param str file_name: The file name with extension and without '/' at the beginning
    """

    conf = load_configuration_from_json_file(file_name)
    conf_as_list = ['test']

    for argument_name, argument_value in conf.items():
        prefix = '--'
        if len(argument_name) == 1:
            prefix = '-'
        conf_as_list.append(prefix+argument_name)
        conf_as_list.append(str(argument_value))

    return conf_as_list
