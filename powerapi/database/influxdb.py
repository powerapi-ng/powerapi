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
import logging
from typing import List, Type
try:
    from influxdb import InfluxDBClient
    from requests.exceptions import ConnectionError as InfluxConnectionError
except ImportError:
    logging.getLogger().info("influx-client is not installed.")

from powerapi.report import Report
from .base_db import BaseDB, DBError


class CantConnectToInfluxDBException(DBError):
    """
    Exception raised to notify that connection to the influx database is impossible
    """


class InfluxDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a InfluxDB database in reading or writing.
    """

    def __init__(self, report_type: Type[Report], uri: str, port, db_name: str, tags: List[str]):
        """
        :param url:             URL of the InfluxDB server
        :param port:            port of the InfluxDB server

        :param db_name:         database name in the influxdb
                                    (ex: "powerapi")

        :param report_type:        Type of the report handled by this database
        :param tags: metadata used to tag metric

        """
        BaseDB.__init__(self, report_type)
        self.uri = uri
        self.port = port
        self.db_name = db_name
        self.tags = tags

        self.client = None

    def __iter__(self):
        raise NotImplementedError()

    def _ping_client(self):
        if hasattr(self.client, 'ping'):
            self.client.ping()
        else:
            self.client.request(url="ping", method='GET', expected_response_code=204)

    def connect(self):
        """
        Override from BaseDB.

        Create the connection to the influxdb database with the current
        configuration (hostname/port/db_name), then check if the connection has
        been created without failure.

        """
        # close connection if reload
        if self.client is not None:
            self.client.close()

        self.client = InfluxDBClient(host=self.uri, port=self.port, database=self.db_name)
        try:
            self._ping_client()
        except InfluxConnectionError as exn:
            raise CantConnectToInfluxDBException('connexion error') from exn

        for db in self.client.get_list_database():
            if db['name'] == self.db_name:
                return

        self.client.create_database(self.db_name)

    def save(self, report: Report):
        """
        Override from BaseDB

        :param report: Report to save
        """
        data = self.report_type.to_influxdb(report, self.tags)
        for tag in data['tags']:
            data['tags'][tag] = str(data['tags'][tag])
        self.client.write_points([data])

    def save_many(self, reports: List[Report]):
        """
        Save a batch of data

        :param reports: Batch of data.
        """

        data_list = list(map(lambda r: self.report_type.to_influxdb(r, self.tags), reports))
        self.client.write_points(data_list)
