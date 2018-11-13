"""
Module csvdb
"""

import csv

from sortedcontainers import SortedDict
from smartwatts.database.base_db import BaseDB
from smartwatts.utils import utils

# Array of field that will not be considered as a group
COMMON_ROW = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class CsvDB(BaseDB):
    """
    CsvDB class
    !!! BAD PERFORMANCE (load in memory) !!!
    """

    def __init__(self, report_model, files_name):
        """
        Parameters:
          @files_name:   list of file name .csv, each one
                         is a different group.
          @report_model: XXXModel object.

        Attributs:
          database:
              keys: (timestamp, sensor, target)
              values: HWPCReport
        """
        BaseDB.__init__(self, report_model)
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
                            'target': row['target']}

                    # Call the report_model and concat both dict
                    specific_dict = self.report_model.from_csvdb(
                        group_name,
                        row)
                    utils.dict_merge(self.database[key], specific_dict)

    def get_next(self):
        """ Override """
        try:
            _, report = self.database.popitem(0)
        except KeyError:
            return None
        return report

    def save(self, json):
        """ Override """
        raise NotImplementedError
