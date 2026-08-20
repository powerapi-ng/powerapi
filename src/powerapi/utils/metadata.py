# Copyright (c) 2026, Inria
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

import re
import unicodedata
from collections.abc import Iterable, Mapping

_INVALID_METADATA_NAME_CHARACTER = re.compile(r'[^A-Za-z0-9_]')


def normalize_metadata_name(name: str, prefix: str) -> str:
    """
    Build a canonical metadata name from a prefix and a source name.

    The combined name is case-folded and converted to ASCII. Characters without ASCII representation are discarded.
    Characters outside ``[A-Za-z0-9_]`` are replaced with underscores.

    :param name: Source metadata name provided by the platform
    :param prefix: Namespace prefix prepended to the source name
    :return: Lowercase, ASCII-only canonical metadata name
    """
    prefixed_name = f'{prefix}{name}'.casefold()
    ascii_prefixed_name = unicodedata.normalize('NFKD', prefixed_name).encode('ascii', 'ignore').decode('ascii')
    return _INVALID_METADATA_NAME_CHARACTER.sub('_', ascii_prefixed_name)


def build_metadata_mapping(names: Iterable[str], prefix: str) -> Mapping[str, str]:
    """
    Map source metadata names to their canonical metadata names.

    Duplicate source names are included once in first-occurrence order.
    Distinct source names that produce the same canonical name are rejected.

    :param names: Source metadata names provided by the platform
    :param prefix: Namespace prefix prepended to every source name
    :return: Mapping from source metadata names to canonical metadata names
    :raises ValueError: If distinct source names produce the same canonical name
    """
    metadata_mapping = {}
    source_by_normalized_name = {}
    for source_name in dict.fromkeys(names):
        normalized_name = normalize_metadata_name(source_name, prefix)
        if normalized_name in source_by_normalized_name:
            previous_source_name = source_by_normalized_name[normalized_name]
            raise ValueError(f'Metadata names {previous_source_name} and {source_name} both normalize to {normalized_name}')

        source_by_normalized_name[normalized_name] = source_name
        metadata_mapping[source_name] = normalized_name

    return metadata_mapping
