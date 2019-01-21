# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import csv

from smartwatts.database.base_db import BaseDB
from smartwatts.report_model.report_model import KEYS_COMMON
from smartwatts.utils import utils

# Array of field that will not be considered as a group
COMMON_ROW = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class CsvBadFilePathError(Exception):
    """
    Exception raised when file is not found
    """


class CsvBadCommonKeys(Exception):
    """
    Exception raised when a common keys is not found
    """


class CsvDB(BaseDB):
    """
    CsvDB class herited from BaseDB

    This class define the behaviour for reading some csv file.
    """

    def __init__(self, report_model, files_name):
        """
        :param list files_name: list of file name .csv
        :param report_model: object that herit from ReportModel and define
                             the type of Report
        :type report_model: martwatts.ReportModel
        """
        BaseDB.__init__(self, report_model)

        #: (list): list of file name .csv
        self.files_name = files_name

        # intern memory
        self.tmp = {
            path_file: {
                'next_line': [],
                'csv': None
            }
            for path_file in files_name
        }

        #: (int): allow to know if we read a new report, or the same
        #: current timestamp
        self.saved_timestamp = utils.timestamp_to_datetime(0)

    def _next(self, path_file):
        """
        Get next row, None otherwise

        :param str path_file: file name we want to read
        """
        try:
            return self.tmp[path_file]['csv'].__next__()
        except StopIteration:
            return None

    def load(self):
        """
        Override from BaseDB.

        Read first line of all the .csv file and check if the pattern is good.
        """

        # Open all files with csv and read first line
        for path_file in self.files_name:
            try:
                self.tmp[path_file]['csv'] = csv.DictReader(open(path_file))
            except FileNotFoundError:
                raise CsvBadFilePathError()
            self.tmp[path_file]['next_line'] = self._next(path_file)

            # Check common key
            for key in KEYS_COMMON:
                if key not in self.tmp[path_file]['next_line']:
                    raise CsvBadCommonKeys()

        # Save the first timestamp
        self.saved_timestamp = utils.timestamp_to_datetime(
            int(self.tmp[self.files_name[0]]['next_line']['timestamp']))

    def get_next(self):
        """
        Override from BaseDB.

        Get the next report from csv files, or None is there is no more.

        :return: The next report
        :rtype: formated JSON from report_model
        """

        # Dict to return
        json = {}

        # Get the current timestamp
        current_timestamp = self.saved_timestamp

        # For all files
        for path_file in self.files_name:

            # While timestamp is lower or equal
            while True:

                # Get the next line
                row = self.tmp[path_file]['next_line']

                # If nothing more, break
                if row is None:
                    break

                # Get the timestamp as datetime
                row_timestamp = utils.timestamp_to_datetime(
                    int(row['timestamp']))

                # If timestamp is higher, we stop here
                if row_timestamp > current_timestamp:
                    if path_file == self.files_name[0]:
                        self.saved_timestamp = row_timestamp
                    break

                # Else if it's the same, we merge
                elif row_timestamp == current_timestamp:
                    utils.dict_merge(
                        json,
                        self.report_model.from_csvdb(path_file.split('/')[-1],
                                                     row))

                # Next line
                self.tmp[path_file]['next_line'] = self._next(path_file)

        if not json:
            return None
        return json

    def save(self, json):
        """
        Not implemented yet.
        """
        raise NotImplementedError()
