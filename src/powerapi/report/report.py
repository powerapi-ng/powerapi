# Copyright (c) 2021, Inria
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

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import NewType, Any
from zlib import crc32

from powerapi.exception import PowerAPIExceptionWithMessage
from powerapi.message import Message

TIMESTAMP_KEY = 'timestamp'
SENSOR_KEY = 'sensor'
TARGET_KEY = 'target'
METADATA_KEY = 'metadata'
GROUPS_KEY = 'groups'

CSV_HEADER_COMMON = [TIMESTAMP_KEY, SENSOR_KEY, TARGET_KEY]
CsvLines = NewType('CsvLines', tuple[list[str], dict[str, str]])

TAGS_NAME_TRANSLATION_TABLE = str.maketrans('.-/', '___')


class BadInputData(PowerAPIExceptionWithMessage):
    """
    Exception raised when input data can't be converted to a Report
    """

    def __init__(self, msg, input_data):
        PowerAPIExceptionWithMessage.__init__(self, msg)
        self.input_data = input_data


class Report(Message):
    """
    Report abstract class.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, metadata: dict[str, Any] | None = None):
        """
        :param timestamp: Timestamp of the measurements.
        :param sensor: Name of the sensor from which the measurements were taken.
        :param target: Name of the target that the measurements refer to.
        """
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.timestamp}, {self.sensor}, {self.target})'

    def __eq__(self, other) -> bool:
        return (isinstance(other, type(self)) and
                self.timestamp == other.timestamp and
                self.sensor == other.sensor and
                self.target == other.target and
                self.metadata == other.metadata)

    @staticmethod
    def _extract_timestamp(ts):
        # Unix timestamp format (in milliseconds)
        if isinstance(ts, int):
            return datetime.fromtimestamp(ts / 1000)

        # datetime object
        if isinstance(ts, datetime):
            return ts

        if isinstance(ts, str):
            try:
                # ISO 8601 date format
                return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                # Unix timestamp format (in milliseconds)
                return datetime.fromtimestamp(int(ts) / 1000)

        raise ValueError('Invalid timestamp format')

    @staticmethod
    def sanitize_tags_name(tags: Iterable[str]) -> dict[str, str]:
        """
        Generate a dict containing the tags name and theirs corresponding sanitized version.

        The tags name are sanitized according to InfluxDB and Prometheus restrictions.
        If a sanitized tag have conflicts (`tag-name` and `tag.name` -> `tag_name`) a hash of the input tag will be
        appended at the end of the sanitized tag name. This allows to have stable tags name in the destination database.
        :param tags: Iterable object containing the tags name
        :return: Dictionary containing the input tag name as key and its sanitized version as value
        """
        sanitized_tags = {tag: tag.translate(TAGS_NAME_TRANSLATION_TABLE) for tag in tags}
        conflict_count = Counter(sanitized_tags.values())
        return {
            tag_orig: (tag_new if conflict_count[tag_new] == 1 else f'{tag_new}_{crc32(tag_orig.encode()):x}')
            for tag_orig, tag_new in sanitized_tags.items()
        }

    @staticmethod
    def flatten_tags(tags: dict[str, Any], separator: str = '_') -> dict[str, Any]:
        """
        Flatten nested dictionaries within a tags dictionary.

        This method takes a dictionary of tags, which may contain nested dictionaries as values, and flattens them into
        a single-level dictionary. Each key in the flattened dictionary is constructed by concatenating the keys from
        the nested dictionaries with their parent keys, separated by the specified separator.

        This is particularly useful for databases that only support canonical (non-nested) types as values.
        :param tags: Input tags dict
        :param separator: Separator to use for the flattened tags name
        :return: Flattened tags dict
        """
        return {
            f"{pkey}{separator}{ckey}" if isinstance(pvalue, dict) else pkey: cvalue for pkey, pvalue in tags.items()
            for ckey, cvalue in (pvalue.items() if isinstance(pvalue, dict) else {pkey: pvalue}.items())
        }
