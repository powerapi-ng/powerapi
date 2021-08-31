# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
from typing import Dict, List, Tuple, Any

from powerapi.report.report import Report, CSV_HEADER_COMMON, BadInputData


CSV_HEADER_POWER = CSV_HEADER_COMMON + ['power', 'socket']


class PowerReport(Report):
    """
    PowerReport stores the power estimation information.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, power: float, metadata: Dict[str, Any]):
        """
        Initialize a Power report using the given parameters.
        :param datetime timestamp: Report timestamp
        :param str sensor: Sensor name
        :param str target: Target name
        :param float power: Power value
        :param dict metadata: Metadata values, can be anything that add useful information
        """
        Report.__init__(self, timestamp, sensor, target)

        self.metadata = metadata
        self.power = power

    def __repr__(self) -> str:
        return 'PowerReport(%s, %s, %s, %f, %s)' % (self.timestamp, self.sensor, self.target, self.power, str(self.metadata))

    @staticmethod
    def from_json(data: Dict) -> Report:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The HWPC report initialized with the given data
        """
        try:
            ts = Report._extract_timestamp(data['timestamp'])
            return PowerReport(ts, data['sensor'], data['target'], data['power'], data['metadata'])
        except KeyError as exn:
            raise BadInputData('no field ' + str(exn.args[0]) + ' in json document')

    @staticmethod
    def from_csv_lines(lines: List[Tuple[str, Dict]]) -> PowerReport:

        if len(lines) != 1:
            raise BadInputData('a power report could only be parsed from one csv line')
        file_name, row = lines[0]

        try:
            sensor_name = row['sensor']
            target = row['target']
            timestamp = Report._extract_timestamp(row['timestamp'])
            power = float(row['power'])
            socket = int(row['socket'])
            core = -1 if 'core' not in row else row['core']
            metadata = {}

            for key in row.keys():
                if key not in CSV_HEADER_POWER:
                    metadata[key] = row[key]
            return PowerReport(timestamp, sensor_name, target, power, metadata)

        except KeyError as exn:
            raise BadInputData('missing field ' + str(exn.args[0]) + ' in csv file ' + file_name)

    @staticmethod
    def to_csv_lines(report: PowerReport, tags: List[str]) -> Tuple[List[str], Dict]:
        line = {
            'sensor': report.sensor,
            'target': report.target,
            'timestamp': int(datetime.timestamp(report.timestamp) * 1000),
            'power': report.power
        }
        for tag in tags:
            if tag not in report.metadata:
                raise BadInputData('no tag ' + tag + ' in power report')
            line[tag] = report.metadata[tag]

        final_dict = {'PowerReport': [line]}
        return CSV_HEADER_POWER, final_dict

    @staticmethod
    def to_virtiofs_db(report: PowerReport) -> Tuple[str, str]:
        """
        return a tuple containing the power value and the name of the file to store the value.
        """
        if 'socket' not in report:
            raise BadInputData('no tag socket in power report')
        filename = 'power_consumption_package' + str(report['socket'])
        power = report.power
        return filename, power

    def _gen_tag(self, metadata_keept):
        tags = {'sensor': self.sensor,
                'target': self.target
                }

        for metadata_name in metadata_keept:
            if metadata_name not in self.metadata:
                raise BadInputData('no tag ' + tag + ' in power report')
            else:
                tags[metadata_name] = self.metadata[metadata_name]

        return tags

    @staticmethod
    def to_influxdb(report: PowerReport, tags: List[str]) -> Dict:
        return {
            'measurement': 'power_consumption',
            'tags': report._gen_tag(tags),
            'time': str(report.timestamp),
            'fields': {
                'power': report.power
            }
        }

    @staticmethod
    def to_prometheus(report: PowerReport, tags: List[str]) -> Dict:
        return {
            'tags': report._gen_tag(tags),
            'time': int(report.timestamp.timestamp()),
            'value': report.power
        }

    @staticmethod
    def to_mongodb(report: PowerReport) -> Dict:
        return PowerReport.to_json(report)

    @staticmethod
    def from_mongodb(data: Dict) -> Report:
        return PowerReport.from_json(data)

