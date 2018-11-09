"""
Abstract Group by rule
"""


class AbstractGroupBy:
    """
    Abstract Group by rule
    """
    def __init__(self, primary=False):
        self.is_primary = primary
        self.fields = None

    def extract(self, report):
        """
        divide a report into multiple report given a group_by rule

        Return: ([(tuple, Report)]) a list all report with their
                identifier
        """
        raise NotImplementedError
