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

from powerapi.utils import Error


class DBError(Error):

    """
    Error raised when an error occuried when using a database
    """
    def __init__(self, msg):
        """
        :param str msg: Message of the error
        """
        super().__init__(msg)
        self.msg = msg


class BaseDB:
    """
    Abstract class which define every common function for database uses.

    This class define every common function that need to be implemented
    by each DB module. A database module correspond to a kind of BDD.
    For example, Mongodb, influxdb, csv are different kind of BDD.
    """

    def __init__(self, report_model, stream_mode):
        """
        :param report_model: object that herit from ReportModel and define
                             the type of Report
        :type report_model: powerapi.ReportModel
        """
        #: (powerapi.ReportModel): Object that herit from ReportModel and
        #: define the type of Report
        self.report_model = report_model

        #: (bool): Stream mode
        self.stream_mode = stream_mode

    def connect(self):
        """
        Function that allow to load the database. Depending of the type,
        different process can happen.

        .. note:: Need to be overrided
        """
        raise NotImplementedError()

    def __iter__(self):
        """
        Create the iterator for get the data
        """
        raise NotImplementedError()

    def __next__(self):
        """
        Allow to get the next data
        """
        raise NotImplementedError()

    def save(self, json):
        """
        Allow to save a json input in the db

        :param dict json: JSON from Report serialize function

        .. note:: Need to be overrided
        """
        raise NotImplementedError()

    def save_many(self, tab_json):
        """
        Allow to save a batch of data

        :param [Dict] tab_json: Batch of data.
        """
        raise NotImplementedError()
