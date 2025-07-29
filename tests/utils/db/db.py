# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

from multiprocessing import Manager
from typing import Iterable

from powerapi.database import ReadableWritableDatabase
from powerapi.report import Report


def define_database_content(content):
    """
    Decorator for defining a database content
    """
    def wrap(func):
        setattr(func, '_content', content)
        return func

    return wrap


REPORT1 = Report(1, 2, 3)
REPORT2 = Report(3, 4, 5)


class SilentFakeDB(ReadableWritableDatabase):
    """
    Database that stores data inside a local queue.
    """

    def __init__(self, content: list | None = None):
        super().__init__()

        self.manager = Manager()
        self.q = self.manager.Queue()

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


def define_database(database):
    """
    Decorator to set the _database
    attribute for individual tests.

    ! If you use this decorator, you need to insert handler in  pytest_generate_tests function !
    ! see tests/unit/test_puller.py::pytest_generate_tests for example  !
    """

    def wrap(func):
        setattr(func, '_database', database)
        return func

    return wrap


def define_report_type(report_type):
    """
    Decorator to set the _report_type
    attribute for individuel tests.

    ! If you use this decorator, you need to insert handler in  pytest_generate_tests function !
    ! see tests/unit/test_puller.py::pytest_generate_tests for example  !
    """

    def wrap(func):
        setattr(func, '_report_type', report_type)
        return func

    return wrap
