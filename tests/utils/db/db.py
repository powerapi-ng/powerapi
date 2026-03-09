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
from contextlib import contextmanager
from datetime import datetime, timezone
from multiprocessing import Manager
from uuid import uuid4

from powerapi.database import ReadableWritableDatabase, ReadFailed, WriteFailed, ConnectionFailed
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


class LocalQueueDatabase(ReadableWritableDatabase):
    """
    Database that stores data inside a local queue.
    """

    def __init__(self, content: list | None = None):
        """
        Initialize a new local queue database.
        :param content: Content to pre-fill the queue with
        """
        super().__init__()

        self.manager = Manager()
        self.q = self.manager.Queue()

        if content is not None:
            self.write(content)

        self.is_connected = False

    def connect(self):
        """
        Connect the database.
        Only used to track the status of the database, this is a no-op under the hood as the database is always "connected".
        """
        self.is_connected = True

    def disconnect(self) -> None:
        """
        Disconnect the database.
        Only used to track the status of the database, this is a no-op under the hood as the database cannot be "disconnected".
        """
        self.is_connected = False

    @staticmethod
    def supported_read_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be retrieved from the database.
        :return: Iterable of report types
        """
        return [Report]

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from the database.
        :param stream_mode: No-Op for this driver, steam mode is not supported
        :return: Iterable of reports
        """
        return [self.q.get() for _ in iter(lambda: not self.q.empty(), False)]

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted by the database.
        :return: Iterable of report types
        """
        return [Report]

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports to the database.
        :param reports: Iterable of reports
        """
        for report in reports:
            self.q.put(report)


class FailingLocalQueueDatabase(LocalQueueDatabase):
    """
    Database that stores data inside a local queue.
    This database can be configured to raise exceptions on the connect/read/write operations.
    """

    def __init__(self, content: list | None = None, fail_connect: bool = False, fail_read: bool = False, fail_write: bool = False):
        """
        Initialize a new failing local queue database.
        :param content: Content to pre-fill the queue with
        :param fail_connect: Whether to raise an exception when doing a connect operation
        :param fail_read: Whether raise an exception when doing a read operation
        :param fail_write: Whether to raise an exception when doing a write operation
        """
        super().__init__(content)

        self.fail_connect = fail_connect
        self.fail_read = fail_read
        self.fail_write = fail_write

    @contextmanager
    def with_failures(self, connect: bool = False, read: bool = False, write: bool = False):
        """
        Temporarily enable failure modes for the selected operations.
        The configured failure modes apply only for the duration of the context and are always reverted on exit.
        :param connect: Whether to raise an exception when doing a connect operation
        :param read: Whether to raise an exception when doing a read operation
        :param write: Whether to raise an exception when doing a write operation
        """
        old_modes = self.fail_connect, self.fail_read, self.fail_write
        try:
            self.fail_connect = connect
            self.fail_read = read
            self.fail_write = write
            yield self
        finally:
            self.fail_connect, self.fail_read, self.fail_write = old_modes

    def connect(self) -> None:
        """
        Connect the database.
        :raises ReadFailed: if the operation is configured to fail
        """
        if self.fail_connect:
            raise ConnectionFailed('This database is setup to always fail its connection')

        super().connect()

    def read(self, stream_mode: bool = False) -> Iterable[Report]:
        """
        Read reports from the database.
        :param stream_mode: No-Op for this driver, steam mode is not supported
        :return: Iterable of reports
        :raises ReadFailed: if the operation is configured to fail
        """
        if self.fail_read:
            raise ReadFailed('This database is setup to always fail its reads')

        return super().read(stream_mode)

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports to the database.
        :param reports: Iterable of reports
        :raises WriteFailed: if the operation is configured to fail
        """
        if self.fail_write:
            raise WriteFailed('This database is setup to always fail its writes')

        super().write(reports)
