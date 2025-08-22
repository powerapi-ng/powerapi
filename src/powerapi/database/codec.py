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

from typing import TypeVar, Generic, Protocol

from powerapi.report import Report


class CodecOptions:
    """
    Configuration and utility container for codec operations.
    Provides optional settings and helper methods that can influence how reports are encoded or decoded.
    """


_ReportType = TypeVar('_ReportType', bound=Report)
_EncodedDataType = TypeVar('_EncodedDataType')

class ReportEncoder(Protocol[_ReportType, _EncodedDataType]):
    """
    Abstract report encoder class.
    Used to encode a report into something usable by the database.
    """

    @staticmethod
    def encode(report: _ReportType, opts: CodecOptions | None = None) -> _EncodedDataType: ...


class ReportDecoder(Protocol[_EncodedDataType, _ReportType]):
    """
    Abstract report decoder class.
    Used to decode the data coming from the database into a report.
    """

    @staticmethod
    def decode(data: _EncodedDataType, opts: CodecOptions | None = None) -> _ReportType: ...


_CodecType = TypeVar('_CodecType', ReportEncoder, ReportDecoder)

class _Registry(Generic[_CodecType]):
    """
    Generic codecs registry class.
    """
    _registry: dict[type[Report], _CodecType]

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._registry = {}  # Ensure each subclass has its own independent registry.

    @classmethod
    def register(cls, report_type: type[Report], codec: _CodecType) -> None:
        """
        Register a report type with its corresponding codec.
        :param report_type: Report type to register
        :param codec: Codec to register
        """
        cls._registry[report_type] = codec

    @classmethod
    def get(cls, report_type: type[Report]) -> _CodecType:
        """
        Get the codec corresponding to the given report type.
        :param report_type: Report type
        :return: The codec
        """
        return cls._registry[report_type]

    @classmethod
    def supported_types(cls) -> set[type[Report]]:
        """
        Get the supported codec types.
        :return: Set containing the supported codec types
        """
        return set(cls._registry.keys())


class ReportEncoderRegistry(_Registry[ReportEncoder]):
    """
    Report encoders registry class.
    Used to manage the report encoders supported by a database.
    """


class ReportDecoderRegistry(_Registry[ReportDecoder]):
    """
    Report decoders registry class.
    Used to manage the report decoders supported by a database.
    """
