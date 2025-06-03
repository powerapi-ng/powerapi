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

import logging
from datetime import timezone

from powerapi.database.base_db import BaseDB
from powerapi.database.exception import ConnectionFailed, WriteFailed
from powerapi.report import PowerReport, Report

try:
    from opentsdb import TSDBClient, TSDBClientException
except ImportError:
    logging.getLogger().info("opentsdb-py is not installed.")


class OpenTSDB(BaseDB):
    """
    OpenTSDB database.
    """

    def __init__(self, report_type: type[Report], host: str, port, metric_name: str):
        """
        :param report_type: Type of report handled by this database
        :param host: Host of the OpenTSDB server
        :param port: Port of the OpenTSDB server
        :param metric_name: Name of the metric where the data will be saved
        """
        super().__init__(report_type)

        self.host = host
        self.port = port
        self.metric_name = metric_name

        self.client = TSDBClient(self.host, self.port, run_at_once=False)

    def __iter__(self):
        raise NotImplementedError()

    def connect(self):
        """
        Create the connection to the openTSDB database with the current
        configuration (hostname/port), then check if the connection has
        been created without failure.
        :raise ConnectionFailed: If connection to the server was not successful
        """
        try:
            self.client.init_client(self.host, self.port)
            self.client.is_alive()
        except TSDBClientException as exn:
            raise ConnectionFailed(f'Failed to connect to the OpenTSDB server: {exn}') from exn

    def disconnect(self):
        """
        Disconnect from the OpenTSDB database.
        """
        self.client.close()

    def save(self, report: PowerReport):
        """
        Save a report into the OpenTSDB database.
        :param report: Report to save
        :raise WriteFailed: If the report was not successfully saved by the database
        """
        try:
            timestamp = int(report.timestamp.replace(tzinfo=timezone.utc).timestamp())
            self.client.send(self.metric_name, report.power, timestamp=timestamp, host=report.target)
        except TSDBClientException as exn:
            raise WriteFailed(f'Failed to save report to OpenTSDB: {exn}') from exn

    def save_many(self, reports: list[PowerReport]):
        """
        Save multiple reports into the OpenTSDB database.
        :param reports: List of reports to save
        """
        for report in reports:
            self.save(report)
