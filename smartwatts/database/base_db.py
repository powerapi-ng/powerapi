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

"""
Module base_db

This module define every common function that need to be implemented
by each DB module. A database module correspond to a kind of BDD.
For example, Mongodb, influxdb, csv are different kind of BDD.
"""


class BaseDB:
    """
    BaseDB class.

    JSON HWPC format:
    {
     'timestamp': $int,
     'sensor': '$str',
     'target': '$str',
     'groups' : {
        '$group_name': {
           '$socket_id': {
               '$core_id': {
                   '$event_name': '$int',
                   ...
               }
               ...
           }
           ...
        }
        ...
     }
    }
    """
    def __init__(self, report_model):
        """
        @report_model: XXXModel Object.
        """
        self.report_model = report_model

    def load(self):
        """
        Allow to load the database
        """
        raise NotImplementedError()

    def get_next(self):
        """
        Return the next report on the db or none if there is none
        """
        raise NotImplementedError()

    def save(self, json):
        """
        Allow to save a json input in the db
        """
        raise NotImplementedError()
