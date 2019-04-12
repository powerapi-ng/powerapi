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

from __future__ import annotations

from datetime import datetime
from typing import Dict
from powerapi.message import Message


class DeserializationFail(Exception):
    """
    Exception raised when the
    in the good format
    """


class Report(Message):
    """
    Report abtract class.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str):
        """
        Initialize a report using the given parameters.
        :param datetime timestamp: Timestamp
        :param str sensor: Sensor name.
        :param str target: Target name.
        """
        self.timestamp = timestamp
        self.sensor = sensor
        self.target = target

    def __str__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, self.timestamp, self.sensor, self.target)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, self.timestamp, self.sensor, self.target)

    def __eq__(self, other):
        return isinstance(other, type(self)) and (repr(other) == repr(self))

    def serialize(self) -> Dict:
        """
        Serialize the report in JSON.
        :return: A string containing the report in JSON format
        """
        return self.__dict__

    @staticmethod
    def deserialize(data: Dict) -> Report:
        """
        Generate a report using the given data.

        :param dict json_data: JSON report.
        """
        raise NotImplementedError()
