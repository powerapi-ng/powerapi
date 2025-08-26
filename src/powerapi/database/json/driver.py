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

from collections.abc import Iterable, Iterator
from io import TextIOWrapper
from os import fsync
from pathlib import Path

from powerapi.database.driver import ReadableDatabase, WritableDatabase
from powerapi.database.exceptions import ConnectionFailed, WriteFailed, ReadFailed
from powerapi.database.json.codecs import ReportDecoders, ReportEncoders
from powerapi.report import Report


class JsonInput(ReadableDatabase):
    """
    JSON input database driver.
    Allow to retrieve reports from a `jsonl` file.
    The input **should** follow the JSON Lines text format. (https://jsonlines.org/)
    """

    def __init__(self, report_type: type[Report], input_filepath: str):
        """
        :param report_type: Type of the report handled by this database
        :param input_filepath: Path to the input file
        """
        self.input_filepath = Path(input_filepath)

        self._report_decoder = ReportDecoders.get(report_type)
        self._file: TextIOWrapper | None = None

    def connect(self) -> None:
        try:
            self._file = open(self.input_filepath, encoding='utf-8')
        except OSError as exn:
            raise ConnectionFailed(f'Failed to open input file: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect the JSON input database driver.
        """
        try:
            self._file.close()
        except OSError:
            # Errors can happen when closing the input file, but nothing can be done in this case.
            pass

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be retrieved from the JSON input database.
        :return: Iterable of report types
        """
        return ReportDecoders.supported_types()

    def _reports_generator(self) -> Iterator[Report]:
        """
        Return a generator that yields reports from the JSON file.
        :return: Iterator of reports
        """
        while True:
            line = self._file.readline()
            if line is None:
                break
            yield self._report_decoder.decode(line)

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from a `jsonl` file.
        :param stream_mode: No-OP, this database driver does not support stream mode.
        :return: Iterable of reports
        :raise: ReadFailed if the read operation fails
        """
        try:
            return self._reports_generator()
        except OSError as exn:
            raise ReadFailed(f'Failed to read reports from input file: {exn}') from exn


class JsonOutput(WritableDatabase):
    """
    JSON output database driver.
    Allow to persist reports to a `jsonl` file.
    The output follows the JSON Lines text format. (https://jsonlines.org/)
    """

    def __init__(self, report_type: type[Report], output_filepath: str):
        """
        :param report_type: Type of the report handled by this database
        :param output_filepath: Path to the output file
        """
        super().__init__()

        self.output_filepath = Path(output_filepath)

        self._report_encoder = ReportEncoders.get(report_type)
        self._file: TextIOWrapper | None = None

    def connect(self) -> None:
        """
        Connect the JSON input database driver.
        :raise: ConnectionFailed if the operation fails
        """
        try:
            self._file = open(self.output_filepath, 'w', encoding='utf-8')
        except OSError as exn:
            raise ConnectionFailed(f'Failed to open output file: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect the JSON input database driver.
        """
        try:
            self._file.flush()
            fsync(self._file.fileno())
            self._file.close()
        except OSError:
            # Errors can happen when closing the output file, but nothing can be done in this case.
            pass

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the JSON database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into a `jsonl` file.
        :param reports: Iterable of reports
        :raise: WriteFailed if the operation fails
        """
        try:
            self._file.writelines([self._report_encoder.encode(report) for report in reports])
        except OSError as exn:
            raise WriteFailed(f'Failed to write reports to output file: {exn}') from exn
