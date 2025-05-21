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

from datetime import datetime
from typing import Any

from powerapi.report.report import Report, BadInputData, CSV_HEADER_COMMON, CsvLines, SENSOR_KEY, TARGET_KEY, \
    TIMESTAMP_KEY, METADATA_KEY, GROUPS_KEY

SOCKET_KEY = 'socket'
CPU_KEY = 'cpu'

CSV_HEADER_HWPC = [*CSV_HEADER_COMMON, SOCKET_KEY, CPU_KEY]


class HWPCReport(Report):
    """
    HWPCReport class

    JSON HWPC format

    .. code-block:: json

        {
         'timestamp': $int,
         'sensor': '$str',
         'target': '$str',
         'groups' : {
            '$group_name': {
               '$socket_id': {
                   '$core_id': {
                       '$event_name': '$int',
                       ...
                   }
                   ...
               }
               ...
            }
            ...
         }
        }
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, groups: dict[str, dict], metadata: dict[str, Any] | None = None):
        """
        :param timestamp: Timestamp of the report
        :param sensor: Sensor name
        :param target: Target name
        :param groups: Events groups
        """
        super().__init__(timestamp, sensor, target, metadata)

        self.groups = groups

    def __repr__(self) -> str:
        return f'HWPCReport({self.timestamp}, {self.sensor}, {self.target}, {sorted(self.groups.keys())})'

    def __eq__(self, other) -> bool:
        if not isinstance(other, HWPCReport):
            return False

        return super().__eq__(other) and self.groups == other.groups

    @staticmethod
    def from_json(data: dict) -> HWPCReport:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The HWPC report initialized with the given data
        """
        try:
            ts = Report._extract_timestamp(data[TIMESTAMP_KEY])
            metadata = {} if METADATA_KEY not in data else data[METADATA_KEY]
            return HWPCReport(ts, data[SENSOR_KEY], data[TARGET_KEY], data[GROUPS_KEY], metadata)
        except TypeError as exn:
            raise BadInputData(f'Invalid input document: {exn.args[0]}', data) from exn
        except KeyError as exn:
            raise BadInputData(f'Missing required field "{exn.args[0]}" from input document', data) from exn
        except ValueError as exn:
            raise BadInputData(f'Unexpected field value in input document: {exn.args}', data) from exn

    @staticmethod
    def to_json(report: HWPCReport) -> dict:
        return vars(report)

    @staticmethod
    def from_mongodb(data: dict) -> HWPCReport:
        """
        :return: a HWPCReport from a dictionary pulled from mongodb
        """
        return HWPCReport.from_json(data)

    @staticmethod
    def to_mongodb(report: HWPCReport) -> dict:
        """
        :return: a dictionary, that can be stored into a mongodb, from a given HWPCReport
        """
        return HWPCReport.to_json(report)

    @staticmethod
    def from_csv_lines(lines: CsvLines) -> HWPCReport:
        """
        :param lines: list of pre-parsed lines. a line is a tuple composed with :
                         - the file name where the line were read
                         - a dictionary where key is column name and value is the value read from the line
        :return: a HWPCReport that contains value from the given lines
        """
        sensor_name = None
        target = None
        timestamp = None
        groups = {}

        for file_name, row in lines:
            group_name = file_name[:-4] if file_name[len(file_name) - 4:] == '.csv' else file_name
            try:
                if sensor_name is None:
                    sensor_name = row[SENSOR_KEY]
                    target = row[TARGET_KEY]
                    timestamp = HWPCReport._extract_timestamp(row[TIMESTAMP_KEY])
                else:
                    if sensor_name != row[SENSOR_KEY]:
                        raise BadInputData('csv line with different sensor name are mixed into one report', row)
                    if target != row[TARGET_KEY]:
                        raise BadInputData('csv line with different target are mixed into one report', row)
                    if timestamp != HWPCReport._extract_timestamp(row[TIMESTAMP_KEY]):
                        raise BadInputData('csv line with different timestamp are mixed into one report', row)

                for _, value in row.items():
                    if not value:
                        raise BadInputData('csv line incomplete', row)

                HWPCReport._create_group(row, groups, group_name)

            except KeyError as exn:
                raise BadInputData('missing field ' + str(exn.args[0]) + ' in csv file ' + file_name, row) from exn
            except ValueError as exn:
                raise BadInputData(exn.args[0], row) from exn

        return HWPCReport(timestamp=timestamp, sensor=sensor_name, target=target, groups=groups)

    @staticmethod
    def _create_group(row, groups, group_name):

        if group_name not in groups:
            groups[group_name] = {}

        if row[SOCKET_KEY] not in groups[group_name]:
            groups[group_name][row[SOCKET_KEY]] = {}

        if row[CPU_KEY] not in groups[group_name][row[SOCKET_KEY]]:
            groups[group_name][row[SOCKET_KEY]][row[CPU_KEY]] = {}

        # We retrieve values for each event group
        for current_key, value in row.items():
            if current_key not in CSV_HEADER_HWPC:
                groups[group_name][row[SOCKET_KEY]][row[CPU_KEY]][current_key] = int(value)
