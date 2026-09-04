# Copyright (c) 2023, Inria
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

from copy import deepcopy
from typing import Any


def string_to_bool(value: str) -> bool:
    """
    Convert a textual boolean value.
    :param value: Textual boolean value.
    :return: Converted boolean.
    :raises ValueError: If the value is not a recognized boolean.
    """
    normalized_value = value.strip().casefold()
    if normalized_value in ('yes', 'y', 'true', 't', '1'):
        return True
    if normalized_value in ('no', 'n', 'false', 'f', '0'):
        return False

    raise ValueError(f'Invalid boolean value: {value}')


def string_to_list(value: str) -> list[str]:
    """
    Transforms a comma separated list to a list of strings.
    :param value: The string to be converted
    :return: List of strings
    """
    if value == '':
        return []

    return [v.strip() for v in value.split(',')]


def merge_dictionaries(*configurations: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge configurations from lowest to highest precedence.

    Later configurations override earlier ones. Inputs are not modified.
    :param configurations: Configuration dictionaries ordered from lowest to highest precedence.
    :return: A new recursively merged configuration dictionary.
    """
    merged = {}

    for configuration in configurations:
        for key, value in configuration.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = merge_dictionaries(merged[key], value)
            else:
                merged[key] = deepcopy(value)

    return merged
