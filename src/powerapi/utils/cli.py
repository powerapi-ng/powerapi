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
