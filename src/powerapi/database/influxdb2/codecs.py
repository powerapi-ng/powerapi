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

from dataclasses import dataclass

from powerapi.database.codec import CodecOptions, ReportEncoder, ReportEncoderRegistry
from powerapi.report import PowerReport, FormulaReport


@dataclass
class EncoderOptions(CodecOptions):
    """
    Encoder options for the InfluxDB database.
    """
    allowed_tags_name: set[str]


class PowerReportEncoder(ReportEncoder[PowerReport, dict]):
    """
    Power Report encoder for the InfluxDB database.
    """

    @staticmethod
    def encode(report: PowerReport, opts: EncoderOptions | None = None) -> dict:
        flattened_tags = report.flatten_tags(report.metadata)
        if opts.allowed_tags_name:
            dynamic_tags = {k: v for k, v in flattened_tags.items() if k in opts.allowed_tags_name}
        else:
            dynamic_tags = flattened_tags

        return {
            'measurement': 'powerrep',
            'tags': {'sensor': report.sensor, 'target': report.target} | dynamic_tags,
            'fields': {'power_estimation': report.power},
            'time': report.timestamp,
        }


class FormulaReportEncoder(ReportEncoder[FormulaReport, dict]):
    """
    Formula Report encoder for the InfluxDB database.
    """

    @staticmethod
    def encode(report: FormulaReport, opts: EncoderOptions | None = None) -> dict:
        return {
            'measurement': 'formularep',
            'tags': {'sensor': report.sensor, 'target': report.target},
            'fields': report.metadata,
            'time': report.timestamp,
        }


class ReportEncoders(ReportEncoderRegistry):
    """
    InfluxDB database encoders registry.
    Contains the report encoders supported by the InfluxDB database.
    """

ReportEncoders.register(PowerReport, PowerReportEncoder)
ReportEncoders.register(FormulaReport, FormulaReportEncoder)
