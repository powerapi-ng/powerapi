# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
from urllib.parse import urlparse
try:
    from influxdb_client import InfluxDBClient, WriteOptions, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    logging.getLogger().info("influx-client2 is not installed.")

from powerapi.report import Report
from .base_db import BaseDB, DBError


class CantConnectToInfluxDBException(DBError):
    """
        Exception raised to notify that connection to the influx database is impossible
    """


class InfluxDB2(BaseDB):
    """
        InfluxDB2 class herited from BaseDB

        Allow to handle a InfluxDB database in reading or writing.
    """

    def __init__(self, report_type: Type[Report], url: str, org: str, bucket_name: str, token: str, tags: List[str],
                 port=None):
        """
            :param report_type:     Type of the report handled by this database
            :param url:             URL of the InfluxDB2 server
            :org:                   Organization related to the database
            :param bucket_name:     database name in the influxdb
                                    (ex: "powerapi")
            :param token:           Access token for readings and writings on database
            :param tags:            metadata used to tag metric
            :param port:            port of the InfluxDB2 server (if not specified in the url)
        """
        BaseDB.__init__(self, report_type)
        self.uri = url

        # We check if the URL has the port or not
        parsed_url = urlparse(url)
        if parsed_url.port is None and port is not None:
            self.uri += ':' + port.__str__()

        self.org = org
        self.token = token
        self.bucket_name = bucket_name
        self.tags = tags

        self.client = None
        self.buckets_api = None
        self.write_api = None
        self.query_api = None

    def __iter__(self):
        raise NotImplementedError()

    def _ping_client(self):
        # if hasattr(self.client, 'ping'):
        self.client.ping()
        # else:
        #    self.client.request(url="ping", method='GET', expected_response_code=204)

    def connect(self):
        """
            Override from BaseDB.

            Create the connection to the influxdb database with the current
            configuration (url:port/bucket_name/org), then check if the connection has
            been created without failure.

        """
        # close connection if reload
        if self.client is not None:
            self.client.close()

        try:

            self.client = InfluxDBClient(url=self.uri, token=self.token, org=self.org)
            self._ping_client()
        except BaseException as exn:
            raise CantConnectToInfluxDBException('connexion error') from exn

        # get apis to working with the database
        self.buckets_api = self.client.buckets_api()
        self.write_api = self.client.write_api(WriteOptions(write_type=SYNCHRONOUS))
        self.query_api = self.client.query_api()

        # A bucket is created only if it does not exist
        if self.buckets_api.find_bucket_by_name(self.bucket_name) is not None:
            return

        self.buckets_api.create_bucket(bucket_name=self.bucket_name)

    def get_db_by_name(self, db_name: str):
        return self.buckets_api.find_bucket_by_name(db_name)

    def save(self, report: Report):
        """
            Override from BaseDB

            :param report: Report to save
        """
        self.save_many([report])

    def save_many(self, reports: List[Report]):
        """
            Save a batch of data

            :param reports: Batch of data.
        """
        data_list = list(map(lambda r: self.report_type.to_influxdb(r, self.tags), reports))
        self.write_api.write(bucket=self.bucket_name, record=data_list)
