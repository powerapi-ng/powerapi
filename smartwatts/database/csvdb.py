"""
Module csv which allow to handle CSV db
"""

import csv

from smartwatts.database.base_db import BaseDB
from smartwatts.report.hwpc_report import HWPCReport
import smartwatts.utils as utils
from sortedcontainers import SortedDict

COMMON_ROW = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class CsvDB(BaseDB):
    """
    CsvDB class
    !!! BAD PERFORMANCE (load in memory) !!!

    basic parameters:
      files_name: ['file1.csv', 'file2.csv']
    """

    def __init__(self, files_name):
        """
        Parameters:
          @files_name: list of file name .csv, each one
                       is a different group.

        Attributs:
          database:
              keys: (timestamp, sensor, target)
              values: HWPCReport
        """
        self.database = SortedDict()
        self.files_name = files_name

    def load(self):
        """ Override """

        # Get all .csv filename
        for path_file in self.files_name:
            with open(path_file) as csv_file:
                csv_reader = csv.reader(csv_file)
                group_name = path_file.split('/')[-1]

                # First line is the fields names
                fieldname = csv_reader.__next__()

                for csv_row in csv_reader:
                    row = {fieldname[i]: csv_row[i] for i in range(
                        len(fieldname))}
                    timestamp = utils.timestamp_to_datetime(
                        int(row['timestamp']))
                    key = (timestamp, row['sensor'], row['target'])

                    # If Report doesn't exist, create it
                    if key not in self.database:
                        self.database[key] = {
                            'timestamp': timestamp,
                            'sensor': row['sensor'],
                            'target': row['target'],
                            'groups': {}}

                    # If group doesn't exist, create it
                    if group_name not in self.database[key]['groups']:
                        self.database[key]['groups'][group_name] = {}

                    # If socket doesn't exist, create it
                    if row['socket'] not in self.database[key]['groups'][
                            group_name]:
                        self.database[key]['groups'][group_name][
                            row['socket']] = {}

                    # If cpu doesn't exist, create it
                    if row['cpu'] not in self.database[key]['groups'][
                            group_name][row['socket']]:
                        self.database[key]['groups'][group_name][
                            row['socket']][row['cpu']] = {}

                    # Add events
                    for k, val in row.items():
                        if k not in COMMON_ROW:
                            self.database[key]['groups'][group_name][
                                row['socket']][row['cpu']][k] = int(val)

    def get_next(self):
        """ Return the next report on the db or none if nothing """
        try:
            _, report = self.database.popitem(0)
        except KeyError:
            return None
        return report
