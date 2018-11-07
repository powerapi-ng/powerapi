"""
Module utils
Define some useful functions
"""

import datetime


def timestamp_to_datetime(timestamp):
    """ Function which create datetime from a timestamp value """
    return datetime.datetime.utcfromtimestamp(timestamp/1000)


def datetime_to_timestamp(date):
    """ Cast a datetime object to a simple timestamp """
    return int(datetime.datetime.timestamp(date)*1000)
