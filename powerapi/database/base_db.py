# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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

    def __init__(self, report_model):
        """
        :param report_model: object that herit from ReportModel and define
                             the type of Report
        :type report_model: powerapi.ReportModel
        """
        #: (powerapi.ReportModel): Object that herit from ReportModel and
        #: define the type of Report
        self.report_model = report_model

    def load(self):
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
