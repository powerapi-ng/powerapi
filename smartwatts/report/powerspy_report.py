"""
Module powerspy_report which define the PowerSpyReport class
"""

from smartwatts.report import Report
from enum import Enum


def powerspy_extract_sensor(report):
    return [(str(report.sensor), report)]

class PowerSpyReport(Report):
    """ PowerSpyReport class """

    def __init__(self, val1=0, val2=0):
        self.val1 = val1
        self.val2 = val2

    def operation(self):
        """ op """
        return self.val1 + self.val2

    def from_json(self, json):
        """
        Get PowerSpyReport from mongodb

        Format:
        {
            val1: first value
            val2: second value
        }
        """
        self.val1 = json['val1']
        self.val2 = json['val2']
