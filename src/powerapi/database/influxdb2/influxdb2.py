# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

import logging

from powerapi.database.base_db import BaseDB
from powerapi.database.exception import ConnectionFailed, WriteFailed
from powerapi.report import Report

try:
    from influxdb_client import InfluxDBClient, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS
    from influxdb_client.client.exceptions import InfluxDBError
    from urllib3.exceptions import HTTPError
except ImportError:
    logging.getLogger().info("influx-client2 is not installed.")


class InfluxDB2(BaseDB):
    """
    InfluxDB2 database.
    """

    def __init__(self, report_type: type[Report], url: str, org: str, bucket_name: str, token: str, tags: list[str]):
        """
        :param report_type: Type of the report handled by this database
        :param url: URL of the InfluxDB2 server
        :org: Organization name
        :param bucket_name: Bucket name
        :param token: Access token to use for authentication
        :param tags: metadata used to tag metric
        :param port: Port of the InfluxDB2 server
        """
        super().__init__(report_type)

        self.uri = url
        self.org = org
        self.token = token
        self.bucket_name = bucket_name
        self.tags = tags

        self.client = InfluxDBClient(self.uri, self.token, org=self.org)
        self.buckets_api = self.client.buckets_api()
        self.write_api = self.client.write_api(WriteOptions(SYNCHRONOUS))
        self.query_api = self.client.query_api()

    def __iter__(self):
        raise NotImplementedError()

    def connect(self):
        """
        Connect to the influxdb2 database.
        """
        try:
            self.client.ready()
        except (OSError, HTTPError, InfluxDBError) as exn:
            raise ConnectionFailed(f'Failed to connect to the InfluxDB server: {exn}') from exn

        if self.buckets_api.find_bucket_by_name(self.bucket_name) is None:
            self.buckets_api.create_bucket(bucket_name=self.bucket_name)

    def disconnect(self):
        """
        Disconnect from the influxdb2 database.
        """
        self.client.close()

    def save(self, report: Report):
        """
        Save a report into the database.
        :param report: Report to save
        """
        self.save_many([report])

    def save_many(self, reports: list[Report]):
        """
        Save multiple reports into the database.
        :param reports: List of reports to save
        """
        try:
            serialized_reports = [self.report_type.to_influxdb(report, self.tags) for report in reports]
            self.write_api.write(self.bucket_name, record=serialized_reports)
        except (OSError, HTTPError, InfluxDBError) as exn:
            raise WriteFailed(f'Failed to save report to InfluxDB: {exn}') from exn
