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
import os

import tests.utils.cli as parent_module


def load_configuration_from_json_file(file_name: str) -> dict:
    """
    Load a json dictionary contained in the given file
    :param str file_name: The file name with extension and without '/' at the begining
    """
    configuration = {}
    path = parent_module.__path__[0]
    with open(path + '/' + file_name, encoding='utf-8') as json_file:
        configuration = json.load(json_file)
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

    conf_as_list.extend(generate_cli_configuration_from_dictionary(configuration=conf))

    return conf_as_list


def generate_cli_configuration_from_dictionary(configuration: dict, group_name: str = '') -> list:
    """
    Generate a list with arguments defined in dictionary. The list always has arguments --arg1_name, arg1_value,
    -arg2_name, arg2_value... Each
    argument name has as prefix '-' if it is short (its length == 1) or '--' if it is long (its length>1)
    :param str configuration: The dictionary with the configuration
    :param str group_name: The name of the group that is currently being created
    """
    conf_as_list = []

    for argument_name, argument_value in configuration.items():
        prefix = '--'
        if len(argument_name) == 1:
            prefix = '-'

        if not isinstance(argument_value, dict):
            conf_as_list.append(prefix + argument_name)
            conf_as_list.append(str(argument_value))

        else:

            if 'type' in argument_value:
                conf_as_list.append(group_name)
                conf_as_list.append(argument_value['type'])
                argument_value.pop('type')
                conf_as_list.append('--name')
                conf_as_list.append(argument_name)
            else:
                group_name = prefix + argument_name

            conf_as_list.extend(generate_cli_configuration_from_dictionary(configuration=argument_value,
                                                                           group_name=group_name))

    return conf_as_list


def define_environment_variables_configuration_from_json_file(file_name: str, simple_argument_prefix: str,
                                                              group_arguments_prefix: list) -> list:
    """
    Define a configuration on os.environ by using the given configuration file and prefix.
    Return a list with the name of created variables
    :param str file_name: The file name with extension and without '/' at the beginning
    :param str simple_argument_prefix: Prefix for the arguments with simple values
    :param list group_arguments_prefix: List of prefix for arguments related to groups
    """

    created_variables = []
    conf = load_configuration_from_json_file(file_name)

    for argument_name, argument_value in conf.items():
        if not isinstance(argument_value, dict):
            var_name = (simple_argument_prefix + argument_name).upper()
            os.environ[var_name] = str(argument_value)
            created_variables.append(var_name)
        else:
            environ_var_prefix = ''
            for group_argument_prefix in group_arguments_prefix:
                if group_argument_prefix.lower().endswith((argument_name + '_').lower()):
                    environ_var_prefix = group_argument_prefix
                    break
            for subgroup_argument_name, subgroup_arguments in argument_value.items():
                for current_subgroup_argument_name, current_subgroup_argument_value in subgroup_arguments.items():
                    var_name = (environ_var_prefix + subgroup_argument_name + '_' +
                                current_subgroup_argument_name).upper()
                    os.environ[var_name] = str(current_subgroup_argument_value)
                    created_variables.append(var_name)

    return created_variables


def remove_environment_variables_configuration(variables_names: list):
    """
    Remove a configuration on os.environ by using the given name list
    :param str variables_names: The list of variables to be removed
    """
    for variable_name in variables_names:
        if variable_name in os.environ:
            os.environ.pop(variable_name)
