# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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
    from prometheus_client import start_http_server, Gauge
except ImportError:
    logging.getLogger().info("prometheus-client is not installed.")


class PrometheusDB(BaseDB):
    """
    Database that exposes the power estimations as metrics in order to be scrapped by a Prometheus instance.
    It can only be used as output (with pusher actors).
    """

    def __init__(self, report_type: type[Report], addr: str, port: int, metric_name: str, metric_desc: str, tags: list[str] | None = None):
        """
        :param report_type: Report type
        :param addr: Address to listen on
        :param port: Port number
        :param metric_name: Exposed metric name
        :param metric_desc: Exposed metric (short) description
        :param tags: List of tags that should be exposed with the metric
        """
        super().__init__(report_type)

        self.listen_address = addr
        self.listen_port = port
        self.metric_name = metric_name
        self.metric_description = metric_desc
        self.metric_tag_names = tags or []

        self.http_server = None
        self.http_server_thread = None

        self.energy_metric = None
        self.energy_metric_label_names = None

    def _init_metrics(self):
        """
        Initialize the Prometheus metrics that will be exposed by the HTTP server.
        """
        self.energy_metric_labels_names = ['sensor', 'target', *self.metric_tag_names]
        self.energy_metric = Gauge(self.metric_name, self.metric_description, self.energy_metric_label_names)

    def connect(self):
        """
        Connect the Prometheus database.
        """
        try:
            self.http_server, self.http_server_thread = start_http_server(self.listen_port, self.listen_address)
            self._init_metrics()
        except (OSError, RuntimeError) as exn:
            raise ConnectionFailed(f'Failed to connect the Prometheus database: {exn}') from exn

    def disconnect(self):
        """
        Disconnect the Prometheus database.
        """
        self.http_server.shutdown()
        self.http_server_thread.join()

    def __iter__(self):
        raise NotImplementedError()

    def save(self, report: Report):
        """
        Save the report into the database.
        :param report: Report to save
        """
        try:
            serialized_report = self.report_type.to_prometheus(report, self.metric_tag_names)
            label_values = [serialized_report['tags'].get(label, '') for label in self.energy_metric_label_names]
            self.energy_metric.labels(*label_values).set(serialized_report['value'])
        except (ValueError, TypeError) as exn:
            raise WriteFailed(f'Failed to save the report to Prometheus: {exn}') from exn

    def save_many(self, reports: list[Report]):
        """
        Save multiple reports into the database.
        :param reports: List of reports to save
        """
        for report in reports:
            self.save(report)
