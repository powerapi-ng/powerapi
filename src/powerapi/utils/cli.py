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


def find_longest_string_in_list(strings: list[str]) -> str:
    """
    Find the longest string from a given list of string.
    :param strings: List of strings
    """
    return max(strings, key=len)


def string_to_bool(bool_value: str):
    """
    Transforms a str to bool according to their content
    """
    return bool_value.lower() in ("yes", "true", "t", "1")


def merge_dictionaries(source: dict, destination: dict) -> dict:
    """
    Recursively merge the source dictionary into destination.
    :param source: Dictionary to be merged
    :param destination: Dictionary where the source will be merged to
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            destination[key] = merge_dictionaries(value, destination[key])
        else:
            destination[key] = value

    return destination


def get_longest_related_suffix(var: str, suffixes: list) -> str:
    """
    Search for the longest suffix of a string variable in a provided list. It returns None if a suffix is not found
    :param var: A string for looking its longest suffix
    :param suffixes: A list of suffixes
    """
    suffix = None

    for current_suffix in suffixes:
        if var.endswith(current_suffix):
            if suffix is None:
                suffix = current_suffix
            elif len(current_suffix) > len(suffix):
                suffix = current_suffix

    return suffix


def to_lower_case_and_replace_separators(strings: list, old_separator: str, new_separator: str) -> list:
    """
    Transform all strings in a provided list to lower case and replace a given separator for a new one
    :param strings: List of string to be converted to lower case
    :param old_separator: The old separator in the list of strings
    :param new_separator: The new separator in the list of strings
    """
    new_strings = []
    for current_string in strings:
        new_strings.append(current_string.lower().replace(old_separator, new_separator))

    return new_strings
