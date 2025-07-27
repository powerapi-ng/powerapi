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

from collections.abc import Iterable
from pathlib import Path

from powerapi.database.csv.codecs import ReportDecoders, ReportEncoders
from powerapi.database.csv.fileio_handlers import MultiCsvFileReader, MultiCsvFileWriter
from powerapi.database.driver import ReadableDatabase, WritableDatabase
from powerapi.database.exception import ConnectionFailed, WriteFailed
from powerapi.report import Report


class CSVInput(ReadableDatabase):
    """
    CSV input database driver.
    Allow to retrieve reports from CSV file(s).
    """

    def __init__(self, report_type: type[Report], input_files: list[str]):
        """
        :param report_type: Type of the report handled by this database
        :param input_files: List of input file paths
        """
        super().__init__()

        self.input_filepaths = [Path(file_path) for file_path in input_files]

        self._input_file_handler = MultiCsvFileReader(self.input_filepaths)
        self._report_decoder = ReportDecoders.get(report_type)

    def connect(self) -> None:
        """
        Connect the CSV input database driver.
        :raise: ConnectionFailed if the operation fails
        """
        try:
            self._input_file_handler.open()
        except OSError as exn:
            raise ConnectionFailed(f'Failed to setup file handler: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect the CSV input database driver.
        """
        self._input_file_handler.close()

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be retrieved from the CSV database.
        :return: Iterable of report types
        """
        return ReportDecoders.supported_types()

    def _reports_generator(self) -> Iterable[Report]:
        """
        Return a generator that yields reports from the database.
        :return: Iterable of reports
        """
        while True:
            rows = self._input_file_handler.next_rows()
            if not rows:
                break
            yield self._report_decoder.decode(rows)

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from the CSV database.
        :param stream_mode: No-Op for this driver, steam mode is not supported
        :return: Iterable of reports
        :raise: ReadFailed if the read operation fails
        """
        return self._reports_generator()


class CSVOutput(WritableDatabase):
    """
    CSV output database driver.
    Allow to persist reports to CSV file(s).
    """

    def __init__(self, report_type: type[Report], output_directory: str):
        """
        :param report_type: Type of the report handled by this database
        :param output_directory: Path to the output directory
        """
        super().__init__()

        self.output_directory = Path(output_directory)

        self._report_encoder = ReportEncoders.get(report_type)
        self._output_file_handler = MultiCsvFileWriter(self.output_directory)

    def connect(self) -> None:
        """
        Connect the CSV output database driver.
        :raise: ConnectionFailed if the operation fails
        """
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            self._output_file_handler.open()
        except OSError as exn:
            raise ConnectionFailed(f'Invalid output directory: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect the CSV output database driver.
        """
        self._output_file_handler.close()

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the CSV database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into CSV file(s).
        :param reports: Iterable of reports
        :raise: WriteFailed if the operation fails
        """
        try:
            for report in reports:
                self._output_file_handler.write_rows(self._report_encoder.encode(report))
        except OSError as exn:
            raise WriteFailed(f'Failed to write reports to CSV files: {exn}') from exn
