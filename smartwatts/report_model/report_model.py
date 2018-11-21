"""
Module report_model
"""

KEYS_COMMON = ['timestamp', 'sensor', 'target']
KEYS_CSV_COMMON = KEYS_COMMON + ['socket', 'cpu']


class ReportModel:
    """
    ReportModel class.
    It define all the function that need to be override if we want
    to get a report from every kind of db.
    """

    def from_mongodb(self, json):
        """ get the mongodb report """
        raise NotImplementedError

    def from_csvdb(self, file_name, row):
        """ get the csvdb report """
        raise NotImplementedError
