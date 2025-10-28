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

from abc import abstractmethod
from collections.abc import Iterable
from threading import Lock
from time import time
from typing import ClassVar

from powerapi.database.codec import ReportEncoder
from powerapi.database.prometheus.codecs import PowerReportEncoder, EncoderOptions
from powerapi.report import PowerReport, Report

try:
    from prometheus_client import Metric
    from prometheus_client.metrics_core import GaugeMetricFamily
    from prometheus_client.registry import Collector
except ImportError:
    Metric = None
    GaugeMetricFamily = None
    Collector = None


class ReportCollector(Collector):
    """
    Base Report Collector class.
    """

    def __init__(self, labels: list[str], samples_ttl: float):
        """
        :param labels: List of labels name to use for the metrics
        :param samples_ttl: Expiration time of the metrics samples in seconds
        """
        super().__init__()

        self.labels = labels
        self.samples_ttl = samples_ttl

    @abstractmethod
    def submit(self, reports: Iterable[Report], encoder: ReportEncoder, encoder_opts: EncoderOptions) -> None: ...


class PowerReportCollector(ReportCollector):
    """
    Power Report Collector class.
    Used to export the power reports as Prometheus metrics.
    """

    def __init__(self, labels: list[str], samples_ttl: float):
        """
        :param labels: List of labels name to use for the metrics
        :param samples_ttl: Expiration time of the metrics samples in seconds
        """
        super().__init__(labels, samples_ttl)

        self._lock = Lock()
        self._metrics: dict[tuple[str, ...], tuple[float, float]] = {}

    def submit(self, reports: Iterable[PowerReport], encoder: PowerReportEncoder, encoder_opts: EncoderOptions) -> None:
        """
        Submit reports to be used as samples for the metrics.
        :param reports: Iterable of PowerReport objects
        :param encoder: PowerReport encoder
        :param encoder_opts: Report encoder options
        """
        with self._lock:
            for report in reports:
                labels, values = encoder.encode(report, encoder_opts)
                self._metrics[labels] = values

    def collect(self) -> Iterable[Metric]:
        """
        Returns Prometheus metrics from collected samples.
        :return: Prometheus metrics to be exported
        """
        gauge = GaugeMetricFamily('power_estimation_watts', 'Estimated power consumption for a target', labels=self.labels, unit='watts')
        current_timestamp = time()

        with self._lock:
            for labels, (timestamp, power_estimation) in self._metrics.items():
                if (current_timestamp - timestamp) < self.samples_ttl:
                    gauge.add_metric(labels, power_estimation, timestamp)

        yield gauge


class ReportProcessorFactory:
    """
    Factory that creates a Prometheus Metrics Collector for a specific report type.
    """
    collectors: ClassVar[dict[type[Report], type[ReportCollector]]] = {
        PowerReport: PowerReportCollector,
    }

    @classmethod
    def create_collector(cls, report_type: type[Report], labels: list[str], samples_ttl: float = 300) -> ReportCollector:
        """
        Creates a Prometheus Metrics Collector for a specific report type.
        :param report_type: Report type to create the report collector for
        :param labels: List of labels name to use for the metrics
        :param samples_ttl: Expiration time of the metrics samples in seconds
        :return: Prometheus Metrics Collector
        """
        try:
            collector_cls = cls.collectors[report_type]
            return collector_cls(labels, samples_ttl)
        except KeyError as exn:
            raise ValueError(f'No metrics collector available for report type: {report_type}') from exn
