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

from collections.abc import Iterable
from datetime import datetime, timezone
from multiprocessing import Manager
from uuid import uuid4

from powerapi.database import ReadableWritableDatabase
from powerapi.report import Report


def make_report(sensor: str = 'pytest', target: str | None = None) -> Report:
    """
    Return a single report.
    :param sensor: Sensor name
    :param target: Target name, random UUID4 if None
    :return: Initialized report
    """
    timestamp = datetime.now(timezone.utc)
    target_name = target if target is not None else str(uuid4())
    return Report(timestamp, sensor, target_name)


def generate_reports(num: int, sensor: str = 'pytest') -> list[Report]:
    """
    Generate the given number of reports.
    :param num: Number of reports to generate
    :param sensor: Name of the sensor
    :return: List of reports
    """
    return [make_report(sensor, f'report-{i}') for i in range(num)]


class SilentFakeDB(ReadableWritableDatabase):
    """
    Database that stores data inside a local queue.
    """

    def __init__(self, content: list | None = None):
        super().__init__()

        self.manager = Manager()
        self.q = self.manager.Queue()

        if content is not None:
            self.write(content)

    def connect(self):
        pass  # no-op in this case, there is nothing to connect to

    def disconnect(self) -> None:
        pass  # no-op in this case, there is nothing to disconnect from

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        return [Report]

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        return [self.q.get() for _ in iter(lambda: not self.q.empty(), False)]

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        return [Report]

    def write(self, reports: Iterable[Report]) -> None:
        for report in reports:
            self.q.put(report)
