# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
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

from collections.abc import Iterable

from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from urllib3.exceptions import HTTPError

from powerapi.database import ConnectionFailed, WriteFailed
from powerapi.database.driver import WritableDatabase
from powerapi.database.influxdb2.codecs import ReportEncoders, EncoderOptions
from powerapi.report import Report


class InfluxDB2(WritableDatabase):
    """
    InfluxDB2 database driver.
    Allow to persist reports to an InfluxDB (version 2) database.
    """

    def __init__(self, report_type: type[Report], url: str, org: str, bucket: str, token: str, tags: list[str]):
        """
        :param report_type: Type of the report handled by this database
        :param url: InfluxDB server URL
        :param org: Organization name
        :param bucket: Bucket name
        :param token: Authentication token
        :param tags: List of allowed tags name, leave empty to allow all tags
        """
        super().__init__()

        self._bucket_name = bucket

        self._client = InfluxDBClient(url, token, org=org)
        self._buckets_api = self._client.buckets_api()
        self._write_api = self._client.write_api()

        self._report_encoder = ReportEncoders.get(report_type)
        self._report_encoder_opts = EncoderOptions(set(tags))

    def connect(self) -> None:
        """
        Connect to the InfluxDB database.
        """
        try:
            self._client.ready()
            if self._buckets_api.find_bucket_by_name(self._bucket_name) is None:
                self._buckets_api.create_bucket(bucket_name=self._bucket_name)
        except (OSError, HTTPError, InfluxDBError) as exn:
            raise ConnectionFailed(f'Failed to connect to the InfluxDB server: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect from the InfluxDB database.
        """
        self._client.close()

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the InfluxDB database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write the reports into the InfluxDB database.
        :param reports: Iterable of reports
        :raise: WriteFailed if the write operation fails
        """
        try:
            encoded_reports = [self._report_encoder.encode(report, self._report_encoder_opts) for report in reports]
            self._write_api.write(self._bucket_name, record=encoded_reports)
        except (OSError, HTTPError, InfluxDBError) as exn:
            raise WriteFailed(f'Failed to save report to the InfluxDB database: {exn}') from exn
