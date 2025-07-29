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

from datetime import datetime
from typing import Any

from powerapi.report.report import Report


class HWPCReport(Report):
    """
    HWPCReport class.
    Stores Hardware Performance Counters samples coming from the HwPC-Sensor.
    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, groups: dict[str, dict], metadata: dict[str, Any] | None = None):
        """
        :param timestamp: Timestamp of the report
        :param sensor: Sensor name
        :param target: Target name
        :param groups: Events groups
        """
        super().__init__(timestamp, sensor, target, metadata)

        self.groups = groups

    def __repr__(self) -> str:
        return f'HWPCReport({self.timestamp}, {self.sensor}, {self.target}, {sorted(self.groups.keys())})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HWPCReport):
            return NotImplemented

        return super().__eq__(other) and self.groups == other.groups
