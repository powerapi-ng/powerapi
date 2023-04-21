# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

import json
from datetime import datetime
from typing import Dict, Any, List

from powerapi.report.report import Report, CSV_HEADER_COMMON

CSV_HEADER_FORMULA_REPORT = CSV_HEADER_COMMON + ['metadata']


class FormulaReport(Report):
    """
    FormulaReport stores information about a formula.
    This is useful to gather information about a running formula in order to debug or compute statistics.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, metadata: Dict[str, Any]):
        """
        Initialize a Formula report using the given parameters.
        :param timestamp: Report timestamp
        :param sensor: Sensor name
        :param target: Target name
        :param metadata: Metadata values, can be anything but should be json serializable
        """
        Report.__init__(self, timestamp, sensor, target)
        self.metadata = metadata

    def __repr__(self) -> str:
        return f'FormulaReport({self.timestamp}, {self.sensor}, {self.target}, {self.metadata})'

    @staticmethod
    def to_csv_lines(report: FormulaReport, **_) -> (List[str], Dict[str, Any]):
        """
        Convert a Formula report into a csv line.
        :param report: Formula report that will be converted
        :return: Tuple containing the csv header and the csv lines
        """

        line = {
            'timestamp': int(datetime.timestamp(report.timestamp) * 1000),
            'sensor': report.sensor,
            'target': report.target,
            'metadata': json.dumps(report.metadata)
        }

        return CSV_HEADER_FORMULA_REPORT, {'FormulaReport': [line]}

    @staticmethod
    def to_mongodb(report: FormulaReport) -> Dict[str, Any]:
        """
        Convert a Formula report into a json document that can be stored into mongodb.
        :return: a dictionary, that can be stored into a mongodb
        """
        return FormulaReport.to_json(report)

    @staticmethod
    def to_influxdb(report: FormulaReport, **_) -> Dict[str, Any]:
        """
        Convert a Formula report into a dict that can be stored into influxdb.
        param report: Formula report that will be converted
        :return: a dictionary, that can be stored into influxdb
        """
        document = {
            'measurement': 'formula_report',
            'tags': {
                'sensor': report.sensor,
                'target': report.target,
            },
            'time': int(datetime.timestamp(report.timestamp) * 1000),
            'fields': report.metadata
        }

        return document
