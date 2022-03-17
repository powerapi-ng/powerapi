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

# author : Lauric Desauw
# Last modified : 17 Mars 2022

from typing import List
from prometheus_client import start_http_server
from powerapi.rx import Destination
from powerapi.exception import DestinationException


class PrometheusDestination(Destination):
    """Observer Class for storing reports produced by an observable in a Prometheus DB"""

    def __init__(
        self,
        uri: str,
        port: int,
        metric_name: str,
        metric_description: str,
        tags: List[str],
    ) -> None:
        """Connect to the Prometheus instance

        Args:
            uri : IP address of the server
            port : port to communicate with the server
            metric_name : metrics to specify to prometheus
            metric_description : the description of the metrics
            tags : tag to add in Prometheus

        """
        super().__init__()
        self.uri = uri
        self.port = port
        self.metric_name = metric_name
        self.metric_description = metric_description
        self.tags = tags

        # Start the server on  http://addr:port/
        start_http_server(self.port, addr=self.address)

    def store_report(self, report):
        """Required method for storing a report

        Args:
            report: The report that will be stored
        """

        self.file.write(report.to_prometheus())
