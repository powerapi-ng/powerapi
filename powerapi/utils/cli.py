# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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

def remove_first_characters(arg: str):
    """
    Remove the two first characters of arg if it has more than 2 characters, otherwise, it removes only the first one.
    :param str arg: The string to remove the first characters
    """
    if len(arg) > 2:
        return arg[2:]
    return arg[1]


def find_longest_string_in_list(string_list: list) -> str:
    """
    Find the largest string contained in the given list
    :param list string_list: list of strings
    """
    max_len = 0
    longest_string = ''
    for name in string_list:
        if len(name) > max_len:
            longest_string = name
            max_len = len(name)
    return longest_string


def string_to_bool(bool_value: str):
    """
    Transforms a str to bool according to their content
    """
    return bool_value.lower() in ("yes", "true", "t", "1")


def merge_dictionaries(source: dict, destination: dict) -> dict:
    """
    Merge the dictionary source into destination
    :param source: Dictionary to be merged
    :param destination: dictionary that will modify with the source content
    """
    if len(source) > 0:
        for current_source_key, current_source_value in source.items():
            if not isinstance(current_source_value, dict) or current_source_key not in destination:
                destination[current_source_key] = current_source_value
            else:
                destination[current_source_key] = merge_dictionaries(current_source_value,
                                                                     destination[current_source_key])

    return destination


def generate_group_configuration_from_environment_variables_dict(environ_vars: dict, prefix: str,
                                                                 var_names: list) -> dict:
    """
    Generate a group configuration by using a dictionary of environment variables.
    :param environ_vars: Dictionary for generating the configuration
    :param prefix: the prefix of the environment variables in environ_vars (all variable starts vy prefix)
    :param var_names: the variables names related to the group configuration (each variable has as suffix a name
    in this list)
    """
    conf = {}

    for environ_var_name, var_value in environ_vars:
        # We remove the prefix : <group_name_var_name> is the result
        suffix_var_name = environ_var_name[len(prefix) - len(environ_var_name):].lower()

        for var_name in var_names:
            # the var_name has to be at the end of the suffix
            var_name_lower_case = var_name.lower()
            if suffix_var_name.endswith(var_name_lower_case):
                # The group's name is at the begining of the
                group_var_name = suffix_var_name[0:suffix_var_name.find(var_name_lower_case) - 1]
                if group_var_name not in conf:
                    conf[group_var_name] = {}
                conf[group_var_name][var_name_lower_case] = var_value
                break
    return conf
