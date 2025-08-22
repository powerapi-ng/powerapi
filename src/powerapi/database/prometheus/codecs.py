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
from powerapi.report import PowerReport


@dataclass
class EncoderOptions(CodecOptions):
    """
    Encoder options for the Prometheus database.
    """
    dynamic_tags_name: list[str]


class PowerReportEncoder(ReportEncoder[PowerReport, tuple[tuple[str, ...], tuple[float, float]]]):
    """
    Power Report encoder for the Prometheus database.
    """

    @staticmethod
    def encode(report: PowerReport, opts: EncoderOptions | None = None) -> tuple[tuple[str, ...], tuple[float, float]]:
        flattened_tags = report.flatten_tags(report.metadata)
        dynamic_tags = [flattened_tags.get(tag_name, 'unknown') for tag_name in opts.dynamic_tags_name]
        return (report.sensor, report.target, *dynamic_tags), (report.timestamp.timestamp(), report.power)


class ReportEncoders(ReportEncoderRegistry):
    """
    Prometheus database encoders registry.
    Contains the report encoders supported by the Prometheus database.
    """

ReportEncoders.register(PowerReport, PowerReportEncoder)
