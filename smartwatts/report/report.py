"""
Module report
"""

from enum import Enum


class Report:
    """ Model base class """

    def __init__(self, hw_id):
        self.hw_id = hw_id

    class GroupBy(Enum):
        """ Enum for GroupBy """
        SENSOR = 1
        SOCKET = 2
        CPU = 3

    def serialize(self):
        """
        return the JSON format of the report
        """
        raise NotImplementedError

    def deserialize(self, json):
        """
        feed the report with the JSON input
        """
        raise NotImplementedError
