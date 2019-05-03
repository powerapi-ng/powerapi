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
from typing import Dict, Any

from powerapi.report import Report


class FormulaReport(Report):
    """
    FormulaReport stores information about a formula.
    This is useful to gather information about a running formula in order to debug or compute statistics.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, metadata: Dict[str, Any]):
        """
        Initialize a Power report using the given parameters.
        :param timestamp: Report timestamp
        :param sensor: Sensor name
        :param target: Target name
        :param metadata: Metadata values, can be anything that add useful information
        """
        Report.__init__(self, timestamp, sensor, target)
        self.metadata = metadata

    def __repr__(self) -> str:
        return 'FormulaReport(%s, %s, %s, %s)' % (self.timestamp, self.sensor, self.target, self.metadata)

    @staticmethod
    def deserialize(data: Dict) -> FormulaReport:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The Formula report initialized with the given data
        """
        return FormulaReport(data['timestamp'], data['sensor'], data['target'], data['metadata'])
