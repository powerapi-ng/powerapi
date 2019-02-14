# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module utils
Define some useful functions
"""

import collections.abc as collections
import datetime


class Error(Exception):
    """
    Error class for more understandable Error class
    """
    def __init__(self, msg):
        """
        :param str msg: Message of the error
        """
        super().__init__(msg)


def timestamp_to_datetime(timestamp):
    """
    Create datetime from a timestamp value

    :param int timestamp:
    :rtype: datetime.datetime
    """
    return datetime.datetime.utcfromtimestamp(timestamp/1000)


def datetime_to_timestamp(date):
    """
    Cast a datetime object to a simple timestamp

    :param datetime.datetime date:
    :rtype: int
    """
    return int(datetime.datetime.timestamp(date)*1000)


def dict_merge(dict1, dict2):
    """
    Recursive dict merge, act like dict.update() but update
    all level and not only top-level.

    :param dict dict1:
    :param dict dict2:

    """
    for key, value in dict2.items():
        if (key in dict1 and isinstance(dict1[key], dict) and
                isinstance(dict2[key], collections.Mapping)):
            dict_merge(dict1[key], dict2[key])
        else:
            dict1[key] = value
