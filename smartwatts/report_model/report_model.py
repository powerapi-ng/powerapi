"""
Module report_model
"""

CSV_COMMON = ['timestamp', 'sensor', 'target', 'socket', 'cpu']


class ReportModel:
    """
    ReportModel class.
    It define all the function that need to be override if we want
    to get a report from every kind of db.
    """

    def from_mongodb(self):
        """ get the mongodb report """
        raise NotImplementedError

    def from_csvdb(self, file_name, row):
        """ get the csvdb report """
        raise NotImplementedError
