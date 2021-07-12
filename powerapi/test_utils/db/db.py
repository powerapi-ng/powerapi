# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from powerapi.database import BaseDB, DBError

class FakeDBError(Exception):
    pass

class FakeDB(BaseDB):

    def __init__(self, content=[], pipe=None, *args, **kwargs):
        BaseDB.__init__(self)
        self._content = content
        self.pipe = pipe
        self.exceptions = [FakeDBError]

    def connect(self):
        if self.pipe is not None:
            self.pipe.send('connected')

    def iter(self, report_model, stream_mode):
        return self._content.__iter__()

    def save(self, report, report_model):
        if self.pipe is not None:
            self.pipe.send(report)

    def save_many(self, reports, report_model):
        if self.pipe is not None:
            self.pipe.send(reports)

class SilentFakeDB(BaseDB):
    """
    An empty Database that don't send log message
    """
    def __init__(self, content=[], pipe=None, *args, **kwargs):
        BaseDB.__init__(self)
        self._content = []
    def connect(self):
        pass

    def iter(self, report_model, stream_mode):
        return self._content.__iter__()

    def save(self, report, report_model):
        pass

    def save_many(self, reports, report_model):
        pass


class CrashDB(BaseDB):

    def __init__(self, *args, **kwargs):
        BaseDB.__init__(self)

    def connect(self):
        raise DBError('crash')

def define_database(database):
    """
    Decorator to set the _database
    attribute for individual tests.

    ! If you use this decorator, you need to insert handler in  pytest_generate_tests function !
    """
    def wrap(func):
        setattr(func, '_database', database)
        return func
    return wrap


def define_report_model(report_model):
    """
    Decorator to set the _report_model
    attribute for individuel tests.

    ! If you use this decorator, you need to insert handler in  pytest_generate_tests function !
    """
    def wrap(func):
        setattr(func, '_report_model', report_model)
        return func
    return wrap
