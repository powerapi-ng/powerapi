# Copyright (c) 2021, INRIA
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

from powerapi.exception import PowerAPIExceptionWithMessage
from powerapi.report import Report


class DBError(PowerAPIExceptionWithMessage):

    """
    Error raised when an error occurred when using a database.
    """
    def __init__(self, msg: str):
        PowerAPIExceptionWithMessage.__init__(self, msg)


class IterDB:
    """
    This class define the interface of a database results iterator.
    """

    def __init__(self, db, report_type: type[Report], stream_mode: bool):
        """
        :param db: Database instance
        :param report_type: Report type to convert the database results into
        :param stream_mode: Define if the iterator should stop when there is no data
        """
        self.db = db
        self.report_type = report_type
        self.stream_mode = stream_mode

    def __iter__(self):
        """
        Return an iterator for the database results.
        """
        raise NotImplementedError()

    def __next__(self) -> Report:
        """
        Return and consume the next database result available.
        """
        raise NotImplementedError()


class BaseDB:
    """
    This class define the interface needed to fetch/save reports from/to a database.
    """

    def __init__(self, report_type: type[Report], exceptions: list[type[Exception]] = None):
        """
        :param report_type: The type of report expected
        :param exceptions: List of exception type raised by the database module
        """
        self.report_type = report_type
        self.exceptions = exceptions or []

    def connect(self):
        """
        Connect to the database.
        """
        raise NotImplementedError()

    def disconnect(self):
        """
        Disconnect from the database.
        """
        raise NotImplementedError()

    def iter(self, stream_mode: bool = False) -> IterDB:
        """
        Create and returns a database results iterator.
        :param stream_mode: Define if we read continuously (streaming) or stop when no data is available
        """
        raise NotImplementedError()

    def save(self, report: Report):
        """
        Save a report to the database.
        :param report: Report to be saved
        """
        raise NotImplementedError()

    def save_many(self, reports: list[Report]):
        """
        Save multiple reports to the database. (batch mode)
        :param reports: List of Report to be saved
        """
        raise NotImplementedError()
