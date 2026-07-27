# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
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

from collections import defaultdict
from datetime import datetime, UTC

from powerapi.database.codec import CodecOptions, ReportEncoder, ReportEncoderRegistry, ReportDecoder, ReportDecoderRegistry
from powerapi.report import PowerReport, FormulaReport, HWPCReport

_SourcedCsvRowsType = dict[str, list[dict[str, str]]]  # filename, rows (column name, value)


class PowerReportEncoder(ReportEncoder[PowerReport, _SourcedCsvRowsType]):
    """
    Power Report encoder for the CSV database.
    """

    @staticmethod
    def encode(report: PowerReport, opts: CodecOptions | None = None) -> _SourcedCsvRowsType:
        return {
            'power': [{
                'timestamp': report.timestamp.isoformat(timespec='milliseconds'),
                'sensor': report.sensor,
                'target': report.target,
                'power': str(report.power)
            }]
        }


class FormulaReportEncoder(ReportEncoder[FormulaReport, _SourcedCsvRowsType]):
    """
    Formula report encoder for the CSV database.
    """

    @staticmethod
    def encode(report: FormulaReport, opts: CodecOptions | None = None) -> _SourcedCsvRowsType:
        return {
            'formula': [{
                'timestamp': report.timestamp.isoformat(timespec='milliseconds'),
                'sensor': report.sensor,
                'target': report.target
            }]
        }


_HWPC_NON_EVENT_COLUMNS = frozenset(('timestamp', 'sensor', 'target', 'socket', 'cpu', 'metadata'))

class HWPCReportDecoder(ReportDecoder[_SourcedCsvRowsType, HWPCReport]):
    """
    HwPC Report decoder for the CSV database.
    """

    @staticmethod
    def decode(data: _SourcedCsvRowsType, opts: CodecOptions | None = None) -> HWPCReport:
        first_row = next(iter(data.values()))[0]
        timestamp = datetime.fromtimestamp(int(first_row['timestamp']) / 1000, tz=UTC)
        sensor = first_row['sensor']
        target = first_row['target']

        groups = {}
        for group_name, rows in data.items():
            event_names = [event_name for event_name in rows[0] if event_name not in _HWPC_NON_EVENT_COLUMNS]
            group = defaultdict(dict)
            for row in rows:
                group[row['socket']][row['cpu']] = {event_name: int(row[event_name]) for event_name in event_names}

            groups[group_name] = dict(group)  # Prevent missing-key access from mutating the decoded report.

        return HWPCReport(timestamp, sensor, target, groups, {})


class ReportEncoders(ReportEncoderRegistry):
    """
    CSV database encoders registry.
    Contains the report encoders supported by the CSV database.
    """

ReportEncoders.register(PowerReport, PowerReportEncoder)
ReportEncoders.register(FormulaReport, FormulaReportEncoder)


class ReportDecoders(ReportDecoderRegistry):
    """
    CSV database decoders registry.
    Contains the report decoders supported by the CSV database.
    """

ReportDecoders.register(HWPCReport, HWPCReportDecoder)
