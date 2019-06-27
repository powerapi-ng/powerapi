# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
try:
    from opentsdb import TSDBClient
except ImportError:
    logging.getLogger().info("opentsdb-py is not installed.")

from typing import List

from powerapi.report import PowerReport, Report
from powerapi.report_model import ReportModel
from powerapi.database import BaseDB, DBError


class CantConnectToOpenTSDBException(DBError):
    pass


class OpenTSDB(BaseDB):
    """
    OpenTSDB class herited from BaseDB

    Allow to handle an OpenTSDB database to save PowerReport.
    """

    def __init__(self, host: str, port, metric_name: str):
        """
        :param str host:             host of the OpenTSDB server
        :param int port:            port of the OpenTSDB server

        :param str metric_name:         mectric name to store


        :param report_model:        XXXModel object. Allow to read specific
                                    report with a specific format in a database
        :type report_model:         powerapi.ReportModel

        """
        BaseDB.__init__(self)
        self.host = host
        self.port = port
        self.metric_name = metric_name

        self.client = None

    def connect(self):
        """
        Override from BaseDB.

        Create the connection to the openTSDB database with the current
        configuration (hostname/port), then check if the connection has
        been created without failure.

        """

        # close connection if reload
        if self.client is not None:
            self.client.close()
            self.client.wait()

        self.client = TSDBClient(host=self.host, port=self.port)

        if not self.client.is_connected() and not self.client.is_alive():
            raise CantConnectToOpenTSDBException('connexion error')

    def save(self, report: PowerReport, report_model: ReportModel):
        """
        Override from BaseDB

        :param report: Report to save
        :param report_model: ReportModel
        """
        self.client.send(self.metric_name, report.power, timestamp=int(report.timestamp.timestamp()),
                         host=report.target)

    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Save a batch of data

        :param reports: Batch of data.
        :param report_model: ReportModel
        """

        for report in reports:
            self.save(report, report_model)
