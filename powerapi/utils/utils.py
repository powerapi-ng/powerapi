"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
