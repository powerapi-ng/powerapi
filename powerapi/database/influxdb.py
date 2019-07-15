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


import logging
try:
    from influxdb import InfluxDBClient
    from requests.exceptions import ConnectionError
except ImportError:
    logging.getLogger().info("influx-client is not installed.")

from typing import List


from powerapi.database import BaseDB, DBError

from powerapi.report import Report
from powerapi.report_model import ReportModel

class CantConnectToInfluxDBException(DBError):
    pass


class InfluxDB(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a InfluxDB database in reading or writing.
    """

    def __init__(self, uri: str, port, db_name: str):
        """
        :param str url:             URL of the InfluxDB server
        :param int port:            port of the InfluxDB server

        :param str db_name:         database name in the influxdb
                                    (ex: "powerapi")

        :param report_model:        XXXModel object. Allow to read specific
                                    report with a specific format in a database
        :type report_model:         powerapi.ReportModel

        """
        BaseDB.__init__(self)
        self.uri = uri
        self.port = port
        self.db_name = db_name

        self.client = None

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
            self.client.ping()
        except ConnectionError:
            raise CantConnectToInfluxDBException('connexion error')

        for db in self.client.get_list_database():
            if db['name'] == self.db_name:
                return

        self.client.create_database(self.db_name)

    def save(self, report: Report, report_model: ReportModel):
        """
        Override from BaseDB

        :param report: Report to save
        :param report_model: ReportModel
        """

        data = report_model.to_influxdb(report.serialize())
        self.client.write_points([data])

    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Save a batch of data

        :param reports: Batch of data.
        :param report_model: ReportModel
        """

        data_list = list(map(lambda r: report_model.to_influxdb(r.serialize()), reports))
        self.client.write_points(data_list)
