# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

import csv
import os

from powerapi.database.base_db import BaseDB, IterDB
from powerapi.database.exception import WriteFailed, ReadFailed
from powerapi.report.report import Report, CSV_HEADER_COMMON
from powerapi.utils import utils

# Array of field that will not be considered as a group
COMMON_ROW = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class CsvIterDB(IterDB):
    """
    IterDB class

    This class allows to browse a database as an iterable
    """

    def __init__(self, db, filenames, report_type, stream_mode):
        """
        """
        super().__init__(db, report_type, stream_mode)

        self.filenames = filenames
        self.tmp_read = {}

        # Add it in the tmp
        for filename in filenames:
            self.tmp_read[filename] = {
                'next_line': [],
                'reader': None,
                'file': None
            }

        # Open all files with csv and read first line
        for filename in self.filenames:
            try:
                self.tmp_read[filename]['file'] = open(filename, encoding='utf-8')
                self.tmp_read[filename]['reader'] = csv.DictReader(self.tmp_read[filename]['file'])
            except OSError as exn:
                raise ReadFailed(f'Failed to open "{filename}" file: {exn.strerror}') from exn

            self.tmp_read[filename]['next_line'] = self._next(filename)

            # Check common key
            for key in CSV_HEADER_COMMON:
                if key not in self.tmp_read[filename]['next_line']:
                    raise ReadFailed(f'Missing column "{key}" in file "{filename}"')

        # Save the first timestamp
        if self.filenames:
            self.saved_timestamp = utils.timestamp_to_datetime(
                int(self.tmp_read[self.filenames[0]]['next_line']['timestamp']))

    def __iter__(self):
        """
        """
        return self

    def _next(self, filename):
        """
        Get next row, None otherwise

        :param str filename: file name we want to read
        """
        try:
            return next(self.tmp_read[filename]['reader'])
        except StopIteration:
            return None

    def _close_file(self):
        for filename in self.filenames:
            if self.tmp_read[filename]['file'] is not None:
                self.tmp_read[filename]['file'].close()

    def __next__(self) -> Report:
        """
        Allow to get the next data
        """
        raw_data = []
        # Get the current timestamp
        current_timestamp = self.saved_timestamp
        previous_target = None
        # For all files

        for path_file in self.filenames:
            # While timestamp is lower or equal
            while True:
                # Get the next line
                row = self.tmp_read[path_file]['next_line']

                # If nothing more, break
                if row is None:
                    # If the first file a no next file, just stop the iteration
                    if not raw_data and path_file == self.filenames[0]:
                        self._close_file()
                        raise StopIteration()
                    break

                # Get the timestamp as datetime
                row_timestamp = utils.timestamp_to_datetime(
                    int(row['timestamp']))
                # If timestamp is higher, we stop here
                if row_timestamp > current_timestamp:
                    if path_file == self.filenames[-1]:
                        self.saved_timestamp = row_timestamp
                    break  # move to next file

                if row_timestamp < current_timestamp:
                    self.tmp_read[path_file]['next_line'] = self._next(path_file)
                    continue

                if previous_target is not None:
                    if row['target'] != previous_target:
                        break  # move to next file
                else:
                    previous_target = row['target']

                # Else if it's the same, we merge
                raw_data.append((path_file.split('/')[-1], row))
                # Next line
                self.tmp_read[path_file]['next_line'] = self._next(path_file)

        if not raw_data:
            self._close_file()
            raise StopIteration()

        report = self.report_type.from_csv_lines(raw_data)

        return report


class CsvDB(BaseDB):
    """
    CsvDB class herited from BaseDB

    This class define the behaviour for reading some csv file.
    a CsvDB instance can be define by its current path
    """

    def __init__(self, report_type: type[Report], tags: list[str], current_path="/tmp/csvdbtest", files=[]):
        """
        :param current_path: Current path where read/write files
        """
        BaseDB.__init__(self, report_type)

        #: (list): list of file name .csv
        self.filenames = []

        #: (str): current path
        self.current_path = current_path if current_path[-1] == '/' else current_path + '/'

        #: (int): allow to know if we read a new report, or the same
        #: current timestamp
        self.saved_timestamp = utils.timestamp_to_datetime(0)
        self.tags = tags

        self.add_files(files)

    ##################
    # Specific CsvDB #
    ##################

    def add_file(self, filename):
        """
        Add a file in the filenames list (it can be relative or absolute path)
        :param filename: Path to file
        """
        # If absolute path
        if filename[0] == '/':
            self.filenames.append(filename)
        else:
            filename = self.current_path + filename
            self.filenames.append(filename)

    def add_files(self, filenames):
        """
        Add list of files in the filenames list (it can be relative or absolute path)
        :param filenames: List of path to file
        """
        for filename in filenames:
            self.add_file(filename)

    def clean_files(self):
        """
        Clean the filenames list
        """
        self.filenames.clear()

    ########################
    # Override from BaseDB #
    ########################

    def iter(self, stream_mode: bool = False) -> CsvIterDB:
        """
        Create the iterator for get the data
        """
        return CsvIterDB(self, self.filenames, self.report_type, stream_mode)

    def connect(self):
        """
        Connect to the csv database.
        """

    def disconnect(self):
        """
        Disconnect from the csv database.
        """

    def save(self, report: Report):
        """
        Allow to save a serialized_report in the db

        :param report: Report
        """
        fixed_header, data = self.report_type.to_csv_lines(report, self.tags)

        # If the repository doesn't exist, create it
        rep_path = self.current_path + report.sensor + "-" + report.target
        os.makedirs(rep_path, exist_ok=True)

        for filename, values in data.items():
            output_filename = f'{rep_path}/{filename}.csv'

            with open(output_filename, 'a+', encoding='utf-8') as csvfile:
                expected_header = fixed_header + sorted(set(values[0].keys()) - set(fixed_header))
                header_exist = False

                csvfile.seek(0)  # Go to beginning of file before reading
                reader = csv.DictReader(csvfile)
                if reader.fieldnames:
                    header_exist = True
                    if reader.fieldnames != expected_header:
                        raise WriteFailed(f"Header are not the same in {output_filename}")

                writer = csv.DictWriter(csvfile, fieldnames=expected_header)
                if not header_exist:
                    writer.writeheader()

                for row in values:
                    writer.writerow(row)

    def save_many(self, reports: list[Report]):
        """
        Allow to save a batch of report

        :param reports: Batch of report.
        """
        for report in reports:
            self.save(report)
