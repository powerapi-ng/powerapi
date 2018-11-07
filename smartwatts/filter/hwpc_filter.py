"""
Module hwpc_filter
"""

from smartwatts.filter import Filter
from smartwatts.report import HWPCReport


class HWPCFilter(Filter):
    """ HWPCFilter class """

    def __init__(self):
        Filter.__init__()

    def get_type(self):
        """ Override """
        return HWPCReport
