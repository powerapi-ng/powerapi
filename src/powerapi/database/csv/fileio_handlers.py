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

from abc import ABC, abstractmethod
from collections.abc import Iterable
from csv import DictReader, DictWriter
from dataclasses import dataclass
from pathlib import Path


class CsvFilesReader(ABC):
    """
    Input CSV File Reader base class.
    """

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def next_rows(self) -> dict[str, list[dict[str, str]]]: ...


class CsvFilesWriter(ABC):
    """
    Output CSV File Writer base class.
    """

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def write_rows(self, rows: dict[str, list[dict[str, str]]]) -> None: ...


@dataclass(eq=True, order=True, frozen=True, slots=True)
class _RowCursor:
    """
    Immutable cursor representing the current row position in a CSV file during parsing.
    """
    timestamp: int
    sensor: str
    target: str


class SingleCsvFileReader:
    """
    Single file CSV reader class.
    Handles reports exported into a single file while using the flat format.
    Requires monotonic timestamps and the rows to be sorted by timestamp/sensor/target to work.
    """

    def __init__(self, input_filepath: Path) -> None:
        """
        :param input_filepath: Path to the input file
        """
        super().__init__()

        self.input_filepath = input_filepath
        self.group_name = input_filepath.stem

        self._file = None
        self._reader = None
        self._row_cursor = None
        self._last_row_buffer = None

    def open(self) -> None:
        """
        Open the input file and initialize the reader.
        :raise: OSError if the file cannot be opened
        """
        self._file = open(self.input_filepath, encoding='utf-8')
        self._reader = DictReader(self._file)

        # Initialize the reader by consuming the first rows of the file.
        # These rows will be discarded and never returned by the iterator.
        # This is not ideal, but simplify considerably the code of the reader.
        self.next_rows()

    def close(self) -> None:
        """
        Close the input file and cleanup the reader context.
        """
        if self._file is None:
            return

        try:
            self._file.close()
        except OSError:
            # Unrecoverable errors can happen when closing the input file.
            pass

        self._reader = None
        self._row_cursor = None
        self._last_row_buffer = None

    def cursor(self) -> _RowCursor:
        """
        Return the current row cursor.
        :return: Row cursor object
        """
        return self._row_cursor

    def next_rows(self, row_cursor: _RowCursor | None = None) -> list[dict[str, str]]:
        """
        Returns the next rows sharing the same timestamp/sensor/target from the input file.
        :param row_cursor: Tuple of str representing the expected row cursor
        :return: List of dict representing the rows as column/value pairs
        """
        rows = []

        if row_cursor is not None and row_cursor != self._row_cursor:
            return rows

        if self._last_row_buffer is not None:
            rows.append(self._last_row_buffer)
            self._last_row_buffer = None

        for row in self._reader:
            current_cursor = _RowCursor(int(row['timestamp']), row['sensor'], row['target'])

            if self._row_cursor is None:
                self._row_cursor = current_cursor

            if current_cursor == self._row_cursor:
                rows.append(row)
            else:
                self._row_cursor = current_cursor
                self._last_row_buffer = row
                break

        return rows


class MultiCsvFileReader(CsvFilesReader):
    """
    Multi-files CSV reader class.
    Handles reports exported into multiple files using the flat format.
    Requires monotonic timestamps and the rows to be sorted by timestamp/sensor/target to work.
    """

    def __init__(self, input_filepaths: Iterable[Path]):
        """
        :param input_filepaths: Iterable of Path to the input files
        """
        super().__init__()

        self.input_filepaths = input_filepaths

        self._file_readers: dict[str, SingleCsvFileReader] = {}

    def open(self):
        """
        Open the input files and initialize theirs corresponding reader.
        :raise: OSError if a file cannot be opened
        """
        for input_filepath in self.input_filepaths:
            file_reader = SingleCsvFileReader(input_filepath)
            file_reader.open()
            self._file_readers[input_filepath.stem] = file_reader

    def close(self):
        """
        Close the input files and cleanup the readers context.
        """
        while self._file_readers:
            _, reader = self._file_readers.popitem()
            reader.close()

    def next_rows(self) -> dict[str, list[dict[str, str]]]:
        """
        Returns the next rows sharing the same timestamp/sensor/target across the input files.
        :return: Dict containing a list of rows per group
        """
        current_cursor = None
        if cursors := [cursor for reader in self._file_readers.values() if (cursor := reader.cursor()) is not None]:
            current_cursor = min(cursors)  # type: ignore[arg-type]

        rows = {}
        for group_name, reader in self._file_readers.items():
            if group_rows := reader.next_rows(current_cursor):
                rows[group_name] = group_rows

        return rows


class SingleCsvFileWriter:
    """
    Single file CSV writer class.
    """

    def __init__(self, output_filepath: Path, fieldnames: list[str]):
        """
        :param output_filepath: Path to the output file
        :param fieldnames: List of column names
        """
        super().__init__()

        self.fieldnames = fieldnames
        self.output_filepath = output_filepath

        self._file = None
        self._writer = None

    def open(self) -> None:
        """
        Open the output file and initialize the writer.
        """
        self._file = open(self.output_filepath, 'w', encoding='utf-8')
        self._writer = DictWriter(self._file, self.fieldnames)
        self._writer.writeheader()

    def close(self) -> None:
        """
        Close the output file.
        """
        if self._file is None:
            return

        try:
            self._file.close()
        except OSError:
            # Unrecoverable errors can happen when closing the output file.
            pass

        self._writer = None
        self._file = None

    def write_rows(self, rows: list[dict[str, str]]) -> None:
        """
        Write rows to the output file.
        :param rows: List of dict representing the rows as column/value pairs
        :raise: OSError if something went wrong during the operation
        """
        self._writer.writerows(rows)


class MultiCsvFileWriter(CsvFilesWriter):
    """
    Multi-file csv writer class.
    Allow to export reports into multiple csv files using the flat format.
    """

    def __init__(self, output_directory: Path):
        """
        :param output_directory: Path to the output directory
        """
        super().__init__()

        self.output_directory = output_directory

        self._file_writers: dict[str, SingleCsvFileWriter] = {}

    def open(self) -> None:
        """
        No-OP.
        The file writer(s) will automatically be created during the first write operation.
        """

    def close(self) -> None:
        """
        Close the output file(s).
        """
        while self._file_writers:
            _, writer = self._file_writers.popitem()
            writer.close()

    def _setup_group_file_writer(self, group_name: str, fieldnames: list[str]) -> SingleCsvFileWriter:
        """
        Set up a file writer for a specific group.
        :param group_name: Name of the group (will be the output filename)
        :param fieldnames: List of column names
        :return: File writer for the given group
        """
        file_writer = SingleCsvFileWriter(self.output_directory / f'{group_name}.csv', fieldnames)
        file_writer.open()

        self._file_writers[group_name] = file_writer
        return file_writer

    def write_rows(self, rows: dict[str, list[dict[str, str]]]) -> None:
        """
        Write rows into output files.
        :param rows: List of dict representing the rows as column/value pairs
        :raise: OSError if a file cannot be opened
        """
        for group_name, group_rows in rows.items():
            file_writer = self._file_writers.get(group_name)
            if file_writer is None:
                fieldnames = list(next(iter(group_rows)).keys())
                file_writer = self._setup_group_file_writer(group_name, fieldnames)

            file_writer.write_rows(group_rows)
