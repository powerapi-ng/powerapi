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
from typing import List, Type

try:
    from prometheus_client import start_http_server, Gauge
except ImportError:
    logging.getLogger().info("prometheus-client is not installed.")

from powerapi.report import Report
from .base_db import BaseDB

DEFAULT_ADDRESS = '127.0.0.1'
DEFAULT_METRIC_DESCRIPTION = 'energy consumption'
DEFAULT_MODEL_VALUE = 'PowerReport'
DEFAULT_PUSHER_NAME = 'pusher_prometheus'
TAGS_KEY = 'tags'
VALUE_KEY = 'value'
TIME_KEY = 'time'

SENSOR_TAG = 'sensor'
TARGET_TAG = 'target'


class BasePrometheusDB(BaseDB):
    """
    Base class to expose data to prometheus instance
    """

    def __init__(self, report_type: Type[Report], port: int, metric_name: str,
                 tags: List[str], metric_description: str = DEFAULT_METRIC_DESCRIPTION, address: str = DEFAULT_ADDRESS):
        BaseDB.__init__(self, report_type)
        self.address = address
        self.port = port
        self.metric_name = metric_name
        self.metric_description = metric_description
        self.tags = tags

    def _init_metrics(self):
        raise NotImplementedError()

    def connect(self):
        """
        Start an HTTP server exposing metrics
        """
        start_http_server(port=self.port, addr=self.address)


class PrometheusDB(BasePrometheusDB):
    """
    Database that expose received raw power estimations as metrics in order to be scrapped by a prometheus instance
    It can only be used with a pusher actor
    """

    def __init__(self, report_type: Type[Report], port: int, address: str, metric_name: str, metric_description: str,
                 tags: List[str]):
        """
        :param address: address that exposes the metric
        :param port: port used to expose the metric
        :param metric_name: the name of the metric
        :param metric_description:  short sentence that describe the metric
        :param tags: metadata used to tag metric
        """
        BasePrometheusDB.__init__(self,
                                  report_type=report_type,
                                  port=port,
                                  address=address,
                                  metric_name=metric_name,
                                  metric_description=metric_description,
                                  tags=tags)

        self.energy_metric = None

        self.current_ts = 0
        self.exposed_measure = {}
        self.measure_for_current_period = {}
        self.metrics_initialized = False

    def __iter__(self):
        raise NotImplementedError()

    def _init_metrics(self):
        if not self.metrics_initialized:
            self.energy_metric = Gauge(self.metric_name, self.metric_description, [SENSOR_TAG, TARGET_TAG] + self.tags)
            self.metrics_initialized = True

    def _expose_data(self, _, measure):
        kwargs = {label: measure[TAGS_KEY][label] for label in measure[TAGS_KEY]}
        try:
            self.energy_metric.labels(**kwargs).set(measure[VALUE_KEY])
        except TypeError:
            self.energy_metric.labels(kwargs).set(measure[VALUE_KEY])

    def _report_to_measure_and_key(self, report):
        value = self.report_type.to_prometheus(report, self.tags)
        key = ''.join([str(value[TAGS_KEY][tag]) for tag in value[TAGS_KEY]])
        return key, value

    def _update_exposed_measure(self):
        for key in self.exposed_measure:
            if key not in self.measure_for_current_period:
                args = self.exposed_measure[key]
                self.energy_metric.remove(*args)
        self.exposed_measure = self.measure_for_current_period
        self.measure_for_current_period = {}

    def save(self, report: Report):
        """
        Override from BaseDB

        :param report: Report to save
        """
        if self.tags is None or not self.tags:
            self.tags = list(report.metadata.keys())
        self._init_metrics()

        key, measure = self._report_to_measure_and_key(report)
        if self.current_ts != measure[TIME_KEY]:
            self.current_ts = measure[TIME_KEY]
            self._update_exposed_measure()

        self._expose_data(key, measure)
        if key not in self.measure_for_current_period:
            args = [measure[TAGS_KEY][label] for label in measure[TAGS_KEY]]
            self.measure_for_current_period[key] = args

    def save_many(self, reports: List[Report]):
        """
        Save a batch of data

        :param reports: Batch of data.
        """
        for report in reports:
            self.save(report)
