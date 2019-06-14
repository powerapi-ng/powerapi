# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from typing import List
from powerapi.report import Report
from powerapi.database.base_db import BaseDB, IterDB
from powerapi.report_model.report_model import CSV_HEADER_COMMON, ReportModel
from powerapi.utils import utils, Error

# Array of field that will not be considered as a group
COMMON_ROW = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class CsvBadFilePathError(Error):
    """
    Error raised when file is not found
    """


class CsvBadCommonKeysError(Error):
    """
    Error raised when a common keys is not found
    """


class HeaderAreNotTheSameError(Error):
    """
    Error raised when the header read in a file doesn't fit the input data
    """


class CsvIterDB(IterDB):
    """
    IterDB class

    This class allows to browse a database as an iterable
    """

    def __init__(self, db, filenames, report_model, stream_mode):
        """
        """
        super().__init__(db, report_model, stream_mode)

        self.filenames = filenames

        # intern memory for reading
        # path_file: {
        #     'next_line': [],
        #     'reader': None,
        #     'file': None
        # }
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
                self.tmp_read[filename]['file'] = open(filename)
                self.tmp_read[filename]['reader'] = csv.DictReader(self.tmp_read[filename]['file'])
            except FileNotFoundError as error:
                raise CsvBadFilePathError(error)
            self.tmp_read[filename]['next_line'] = self._next(filename)

            # Check common key
            for key in CSV_HEADER_COMMON:
                if key not in self.tmp_read[filename]['next_line']:
                    raise CsvBadCommonKeysError("Wrong columns keys")

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
            return self.tmp_read[filename]['reader'].__next__()
        except StopIteration:
            return None

    def __next__(self) -> Report:
        """
        Allow to get the next data
        """
        # Dict to return
        json = {}

        # Get the current timestamp
        current_timestamp = self.saved_timestamp

        # For all files
        for path_file in self.filenames:

            # While timestamp is lower or equal
            while True:

                # Get the next line
                row = self.tmp_read[path_file]['next_line']

                # If nothing more, break
                if row is None:
                    break

                # Get the timestamp as datetime
                row_timestamp = utils.timestamp_to_datetime(
                    int(row['timestamp']))

                # If timestamp is higher, we stop here
                if row_timestamp > current_timestamp:
                    if path_file == self.filenames[0]:
                        self.saved_timestamp = row_timestamp
                    break

                # Else if it's the same, we merge
                elif row_timestamp == current_timestamp:
                    utils.dict_merge(
                        json,
                        self.report_model.from_csvdb(path_file.split('/')[-1], row))

                # Next line
                self.tmp_read[path_file]['next_line'] = self._next(path_file)

        if not json:
            # Close files
            for filename in self.filenames:
                if self.tmp_read[filename]['file'] is not None:
                    self.tmp_read[filename]['file'].close()
            raise StopIteration()

        return self.report_model.get_type().deserialize(json)


class CsvDB(BaseDB):
    """
    CsvDB class herited from BaseDB

    This class define the behaviour for reading some csv file.
    a CsvDB instance can be define by his ReportModel and its current path
    """

    def __init__(self, current_path="/tmp/csvdbtest", files=[]):
        """
        :param current_path: Current path where read/write files
        """
        super().__init__()

        #: (list): list of file name .csv
        self.filenames = []

        #: (str): current path
        self.current_path = current_path if current_path[-1] == '/' else current_path + '/'

        #: (int): allow to know if we read a new report, or the same
        #: current timestamp
        self.saved_timestamp = utils.timestamp_to_datetime(0)

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

    def iter(self, report_model: ReportModel, stream_mode: bool) -> CsvIterDB:
        """
        Create the iterator for get the data
        """
        return CsvIterDB(self, self.filenames, report_model, stream_mode)

    def connect(self):
        """
        Override from BaseDB.

        Nothing to do with CSV, because it's just files operations.
        """
        pass

    def save(self, report: Report, report_model: ReportModel):
        """
        Allow to save a serialized_report in the db

        :param report: Report
        :param report_model: ReportModel
        """
        serialized_report = report.serialize()
        csv_header, data = report_model.to_csvdb(serialized_report)

        # If the repository doesn't exist, create it
        rep_path = self.current_path + serialized_report['sensor'] + "-" + serialized_report['target']
        try:
            os.makedirs(rep_path)
        except FileExistsError:
            pass

        for filename, values in data.items():
            rep_path_with_file = rep_path + '/' + filename + '.csv'

            # Get the header and check if it's ok
            # TODO: inefficient
            for value in values:
                header = csv_header + sorted(list(set([event_key for event_key, _ in value.items()]) - set(csv_header)))
                header_exist = False
                try:
                    with open(rep_path_with_file) as csvfile:
                        reader = csv.DictReader(csvfile)
                        if reader.fieldnames:
                            header_exist = True

                        if header != reader.fieldnames:
                            raise HeaderAreNotTheSameError("Header are not the same in " + rep_path_with_file)
                        csvfile.close()
                except FileNotFoundError:
                    pass

                # Write
                with open(rep_path_with_file, 'a') as csvfile:
                    writer = csv.DictWriter(csvfile, header)
                    if not header_exist:
                        writer.writeheader()
                    writer.writerow(value)
                    csvfile.close()

    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Allow to save a batch of report

        :param reports: Batch of report.
        :param report_model: ReportModel
        """
        # TODO: Inefficient
        for report in reports:
            self.save(report, report_model)
