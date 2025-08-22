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

import json
from datetime import datetime

from powerapi.database.codec import CodecOptions, ReportEncoder, ReportEncoderRegistry, ReportDecoder, ReportDecoderRegistry
from powerapi.report import Report, PowerReport, FormulaReport, HWPCReport


class ExtendedJsonEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that handles unsupported report attribute types.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


class GenericReportEncoder(ReportEncoder[Report, str]):
    """
    Generic Report encoder for the JSON database.
    Can be used to encode any Report objects into JSON. (compact format)
    """

    @staticmethod
    def encode(report: Report, opts: CodecOptions | None = None) -> str:
        return json.dumps(vars(report), cls=ExtendedJsonEncoder, indent=None, separators=(',', ':')) + '\n'


class HWPCReportDecoder(ReportDecoder[str, HWPCReport]):
    """
    HwPC Report decoder for the CSV database.
    """

    @staticmethod
    def decode(data: str, opts: CodecOptions | None = None) -> HWPCReport:
        doc = json.loads(data)
        timestamp = datetime.fromisoformat(doc['timestamp'])
        return HWPCReport(timestamp, doc['sensor'], doc['target'], doc['groups'], doc['metadata'])


class ReportEncoders(ReportEncoderRegistry):
    """
    JSON database encoders registry.
    Contains the report encoders supported by the JSON database.
    """

ReportEncoders.register(PowerReport, GenericReportEncoder)
ReportEncoders.register(FormulaReport, GenericReportEncoder)


class ReportDecoders(ReportDecoderRegistry):
    """
    JSON database decoders registry.
    Contains the report decoders supported by the JSON database.
    """

ReportDecoders.register(HWPCReport, HWPCReportDecoder)
