# Copyright (c) 2021, INRIA
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

from typing import Dict, Any

from powerapi.report.report import Report, BadInputData, CSV_HEADER_COMMON, CsvLines


CSV_HEADER_PROCFS = CSV_HEADER_COMMON + ['socket', 'cpu', 'usage', 'global_cpu_usage']


class ProcfsReport(Report):
    """
    ProcfsReport class
    JSON Procfs format
    {
    timestamp: int
    sensor: str,
    target: str,
    usage: [ {cgroup_name: str, usage: float} ]
    }


    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, usage: Dict, global_cpu_usage: float, metadata: Dict[str, Any] = {}):
        """
        Initialize an Procfs report using the given parameters.
        :param datetime timestamp: Timestamp of the report
        :param str sensor: Sensor name
        :param str target: Target name
        :param Dict[str,float] usage : CGroup name and cpu_usage
        :param float global_cpu_usage : The global CPU usage, with untracked process
        """
        Report.__init__(self, timestamp, sensor, target, metadata)

        #: (dict): Events groups
        self.usage = usage
        self.global_cpu_usage = global_cpu_usage

    def __repr__(self) -> str:
        return 'ProcfsReport(%s, %s, %s, %s, %s)' % (self.timestamp, self.sensor, self.target, sorted(self.usage.keys()), str(self.metadata))

    @staticmethod
    def from_json(data: Dict) -> ProcfsReport:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The Procfs report initialized with the given data
        """
        try:
            ts = Report._extract_timestamp(data['timestamp'])
            metadata = {} if 'metadata' not in data else data['metadata']
            return ProcfsReport(ts, data['sensor'], data['target'], data['usage'], data['global_cpu_usage'], metadata)
        except KeyError as exn:
            raise BadInputData('no field ' + str(exn.args[0]) + ' in json document', data) from exn
        except ValueError as exn:
            raise BadInputData(exn.args[0], data) from exn

    @staticmethod
    def to_json(report: ProcfsReport) -> Dict:
        return report.__dict__

    @staticmethod
    def from_mongodb(data: Dict) -> ProcfsReport:
        """ Extract a PorcfsReport fropm a mongo DB"""
        return ProcfsReport.from_json(data)

    @staticmethod
    def to_mongodb(report: ProcfsReport) -> Dict:
        """ Export a ProcfsReport to a mongo DB"""
        return ProcfsReport.to_json(report)

    @staticmethod
    def from_csv_lines(lines: CsvLines) -> ProcfsReport:
        """ Extract a ProcfsReport from a csv"""
        sensor_name = None
        target = None
        timestamp = None
        usage = {}
        global_cpu_usage = None
        metadata = {}
        for file_name, row in lines:
            cgroup_name = file_name[:-4] if file_name[len(file_name) - 4:] == '.csv' else file_name
            try:
                if sensor_name is None:
                    sensor_name = row['sensor']
                    target = row['target']
                    timestamp = Report._extract_timestamp(row['timestamp'])
                    global_cpu_usage = row['global_cpu_usage']
                else:
                    if sensor_name != row['sensor']:
                        raise BadInputData('csv line with different sensor name are mixed into one report', {})
                    if target != row['target']:
                        raise BadInputData('csv line with different target are mixed into one report', {})
                    if timestamp != ProcfsReport._extract_timestamp(row['timestamp']):
                        raise BadInputData('csv line with different timestamp are mixed into one report', {})
                    if global_cpu_usage != row['global_cpu_usage']:
                        raise BadInputData('Different cpu usage are provided in one report', {})

                ProcfsReport._create_cgroup(row, cgroup_name, usage)

                for key, value in row.items():
                    if key not in CSV_HEADER_PROCFS:
                        metadata[key] = value

            except KeyError as exn:
                raise BadInputData('missing field ' + str(exn.args[0]) + ' in csv file ' + file_name, {}) from exn
            except ValueError as exn:
                raise BadInputData(exn.args[0], row) from exn

        return ProcfsReport(timestamp, sensor_name, target, usage, global_cpu_usage, metadata)

    @staticmethod
    def _create_cgroup(_, cgroup_name, usage):
        if cgroup_name not in usage:
            usage[cgroup_name] = {}


def create_report_root(cgroup_list, timestamp=datetime.fromtimestamp(0), sensor='toto', target='all'):
    """ Create a default procfs report """
    sensor = ProcfsReport(timestamp=timestamp, sensor=sensor, target=target, usage={}, global_cpu_usage=0)
    for (cgroup_id, cpu_usage) in cgroup_list:
        sensor.usage[cgroup_id] = cpu_usage
    return sensor
