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

from powerapi.database.codec import CodecOptions, ReportEncoder, ReportEncoderRegistry, ReportDecoder, ReportDecoderRegistry
from powerapi.report import PowerReport, FormulaReport, HWPCReport


class PowerReportEncoder(ReportEncoder[PowerReport, dict]):
    """
    Power Report encoder for the MongoDB database.
    """

    @staticmethod
    def encode(report: PowerReport, opts: CodecOptions | None = None) -> dict:
        return vars(report)

class FormulaReportEncoder(ReportEncoder[FormulaReport, dict]):
    """
    Formula report encoder for the MongoDB database.
    """

    @staticmethod
    def encode(report: FormulaReport, opts: CodecOptions | None = None) -> dict:
        return vars(report)

class HWPCReportDecoder(ReportDecoder[dict, HWPCReport]):
    """
    HwPC Report decoder for the MongoDB database.
    """

    @staticmethod
    def decode(data: dict, opts: CodecOptions | None = None) -> HWPCReport:
        return HWPCReport(data['timestamp'], data['sensor'], data['target'], data['groups'], data.get('metadata', {}))


class ReportEncoders(ReportEncoderRegistry):
    """
    MongoDB database encoders registry.
    Contains the report encoders supported by the MongoDB database.
    """

ReportEncoders.register(PowerReport, PowerReportEncoder)
ReportEncoders.register(FormulaReport, FormulaReportEncoder)

class ReportDecoders(ReportDecoderRegistry):
    """
    MongoDB database decoders registry.
    Contains the report decoders supported by the MongoDB database.
    """

ReportDecoders.register(HWPCReport, HWPCReportDecoder)
