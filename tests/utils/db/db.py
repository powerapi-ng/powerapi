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

from powerapi.database import BaseDB, DBError
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


class FakeDBError(Exception):
    """
    Exception raised to crash the db
    """


class FakeDB(BaseDB):
    """
    Fake DB for testing purposes
    """
    def __init__(self, content=[]):
        BaseDB.__init__(self, Report)
        self._content = content

        self.manager = Manager()
        self.q = self.manager.Queue()

    def connect(self):
        self.q.put('connected', block=False)

    def iter(self, stream_mode: bool = False):
        return iter(self._content)

    def save(self, report):
        self.q.put(report, block=False)

    def save_many(self, reports):
        self.q.put(reports, block=False)


class SilentFakeDB(BaseDB):
    """
    An empty Database that don't send information through the pipe
    """

    def __init__(self, content=[]):
        BaseDB.__init__(self, Report)
        self._content = content

        self.manager = Manager()
        self.q = self.manager.Queue()

    def connect(self):
        pass

    def iter(self, stream_mode: bool = False):
        return iter(self._content)

    def save(self, report):
        self.q.put(report, block=False)

    def save_many(self, reports):
        self.q.put(reports, block=False)


class CrashDB(BaseDB):
    """
    FakeDB that crash when using its connect method
    """

    def __init__(self):
        BaseDB.__init__(self, Report)

    def connect(self):
        raise DBError('crash')


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
