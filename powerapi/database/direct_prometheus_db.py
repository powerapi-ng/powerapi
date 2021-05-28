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
from typing import List

try:
    from prometheus_client import start_http_server, Gauge
except ImportError:
    logging.getLogger().info("prometheus-client is not installed.")

from powerapi.database import BaseDB
from powerapi.report import Report
from powerapi.report_model import ReportModel

class DirectPrometheusDB(BaseDB):
    """
    Database that expose received data as metric in order to be scrapped by a prometheus instance
    Could only be used with a pusher actor
    """

    def __init__(self, port: int, address: str, metric_name: str, metric_description: str, report_model: ReportModel):
        """
        :param address:             address that expose the metric
        :param port:
        :param metric_name:
        :param metric_description:  short sentence that describe the metric
        :param report_model:        model describing the receved report
        """
        BaseDB.__init__(self)
        self.address = address
        self.port = port
        self.metric_name = metric_name
        self.metric_description = metric_description
        self.report_model = report_model

        self.energy_metric = None

        self.current_ts = 0
        self.exposed_measure = {}
        self.measure_for_current_period = {}

    def connect(self):
        """
        Start a HTTP server exposing one metric
        """
        self.energy_metric = Gauge(self.metric_name, self.metric_description, self.report_model.get_tags())
        start_http_server(self.port)

    def _expose_data(self, key, measure):
        kwargs = {label: measure['tags'][label] for label in self.report_model.get_tags()}
        try:
            self.energy_metric.labels(**kwargs).set(measure['value'])
        except TypeError:
            self.energy_metric.labels(kwargs).set(measure['value'])

    def _report_to_measure_and_key(self, report):
        value = self.report_model.to_prometheus(report.serialize())
        key = ''.join([str(value['tags'][tag]) for tag in self.report_model.get_tags()])
        return key, value

    def _update_exposed_measure(self):
        updated_exposed_measure = {}

        for key in self.exposed_measure:
            if key not in self.measure_for_current_period:
                args = self.exposed_measure[key]
                self.energy_metric.remove(*args)
        self.exposed_measure = self.measure_for_current_period
        self.measure_for_current_period = {}
        
    def save(self, report: Report, report_model: ReportModel):
        """
        Override from BaseDB

        :param report: Report to save
        :param report_model: ReportModel
        """
        key, measure = self._report_to_measure_and_key(report)
        if self.current_ts != measure['time']:
            self.current_ts = measure['time']
            self._update_exposed_measure()
            
        self._expose_data(key, measure)
        if key not in self.measure_for_current_period:
            args = [measure['tags'][label] for label in self.report_model.get_tags()]
            self.measure_for_current_period[key] = args

    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Save a batch of data

        :param reports: Batch of data.
        :param report_model: ReportModel
        """
        for report in reports:
            self.save(report, report_model)
