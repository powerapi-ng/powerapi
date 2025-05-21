# Copyright (c) 2021, Inria
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

from datetime import datetime
from typing import Any

from .report import Report


class ControlReport(Report):
    """
    EventReport stores information about an event.
    This is useful to control external tools via a producer/consumer job queue.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, action: str, parameters: list, metadata: dict[str, Any] | None = None):
        """
        :param timestamp: Report timestamp
        :param sensor: Sensor name
        :param target: Target name
        :param action: Action name
        :param parameters: Parameter values
        """
        super().__init__(timestamp, sensor, target, metadata)

        self.action = action
        self.parameters = parameters

    def __repr__(self) -> str:
        return f'ControlReport({self.timestamp}, {self.sensor}, {self.target}, {self.action}, {self.parameters})'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ControlReport):
            return False

        return super().__eq__(other) and self.action == other.action and self.parameters == other.parameters

    @staticmethod
    def from_json(data: dict) -> ControlReport:
        """
        :return: a dictionary, that can be converted into json format, from a given ControlReport
        """
        metadata = {} if 'metadata' not in data else data['metadata']
        return ControlReport(data['timestamp'], data['sensor'], data['target'], data['action'], data['parameters'], metadata)

    @staticmethod
    def from_mongodb(data: dict) -> ControlReport:
        """
        :return: a ControlReport from a dictionary pulled from mongodb
        """
        return ControlReport.from_json(data)

    @staticmethod
    def to_mongodb(report: ControlReport) -> dict:
        """
        :return: a dictionary, that can be stored into a mongodb, from a given ControlReport
        """
        return vars(report)
