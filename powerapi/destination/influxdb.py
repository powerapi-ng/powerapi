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
# Last modified : 6 April 2022

from typing import List
from influxdb import InfluxDBClient
from requests.exceptions import ConnectionError as InfluxConnectionError
from powerapi.rx import Destination
from powerapi.exception import DestinationException


class InfluxDestination(Destination):
    """Observer Class for storing reports produced by an observable in a file"""

    def __init__(self, uri: str, port: int, db_name: str) -> None:
        """Open the file if it exists and create it otherwise

        Args:
            uri : IP address of the server
            port : network port to communicate with the server
            db_name : name of the database in the Influx instance

        """
        super().__init__()
        self.__name__ = "InfluxDestination"
        self.uri = uri
        self.port = port
        self.db_name = db_name

        try:
            self.client = InfluxDBClient(
                host=self.uri, port=self.port, database=self.db_name
            )
        except ValueError as exn:
            raise DestinationException(
                self.__name__, "can't connect to the DB : port error"
            ) from exn

        try:
            self.client.ping()

        except InfluxConnectionError as exn:
            raise DestinationException(self.__name__, "can't connect to DB") from exn

        for db in self.client.get_list_database():
            if db["name"] == self.db_name:
                return
        self.client.create_database(self.db_name)

    def store_report(self, report):
        """Required method for storing a report

        Args:
            report: The report that will be stored
        """
        data = report.to_influx()

        self.client.write_points([data])

    def on_completed(self) -> None:
        """This method is called when the source finished"""
        self.client.close()

    def on_error(self, err) -> None:
        """This method is called when the source has an error"""
        self.client.close()
        raise DestinationException(self.__name__, " : catched exception") from err
