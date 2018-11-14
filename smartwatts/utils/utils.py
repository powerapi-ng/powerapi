"""
Module utils
Define some useful functions
"""

import collections
import datetime


def timestamp_to_datetime(timestamp):
    """ Function which create datetime from a timestamp value """
    return datetime.datetime.utcfromtimestamp(timestamp/1000)


def datetime_to_timestamp(date):
    """ Cast a datetime object to a simple timestamp """
    return int(datetime.datetime.timestamp(date)*1000)


def dict_merge(dict1, dict2):
    """
    Recursive dict merge, act like dict.update() but update
    all level and not only top-level.
    """
    for key, value in dict2.items():
        if (key in dict1 and isinstance(dict1[key], dict) and
                isinstance(dict2[key], collections.Mapping)):
            dict_merge(dict1[key], dict2[key])
        else:
            dict1[key] = value
