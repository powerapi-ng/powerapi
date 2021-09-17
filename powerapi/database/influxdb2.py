# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    #from influxdb import InfluxDBClient
    from requests.exceptions import ConnectionError
except ImportError:
    logging.getLogger().info("influx_client is not installed.")

from typing import List


from powerapi.database import BaseDB, DBError

from powerapi.report import Report
from powerapi.report_model import ReportModel

class CantConnectToInfluxDB2Exception(DBError):
    pass


class InfluxDB2(BaseDB):
    """
    MongoDB class herited from BaseDB

    Allow to handle a InfluxDB database in reading or writing.
    """

    def __init__(self, uri: str, port: int, token: str, org: str, bucket: str):
        """
        :param str url:             URL of the InfluxDB server
        :param int port:            port of the InfluxDB server

        :param str db_name:         database name in the influxdb
                                    (ex: "powerapi")
        
        :param str token            access token Needed to connect to the influxdb instance

        :param str org              org that holds the data (??)
        
        :param str bucket           bucket where the data is going to be stored
        
        :param report_model:        XXXModel object. Allow to read specific
                                    report with a specific format in a database
        :type report_model:         powerapi.ReportModel

        """
        BaseDB.__init__(self)
        self.uri = uri
        self.port = port
        self.complete_url ="http://%s:%s" %(   self.uri , str(self.port))
        #self.db_name = db_name
            
        self.token=token
        self.org = org
        self.org_id = None
        self.bucket = bucket

        self.client = None
        self.write_api= None

    def _ping_client(self):
        if hasattr(self.client, 'health'):
            self.client.health()
        else:
            self.client.request(url="ping", method='GET', expected_response_code=204)

    def connect(self):
        """
        Override from BaseDB.

        Create the connection to the influxdb database with the current
        configuration (hostname/port/db_name), then check if the connection has
        been created without failure.

        """

        # close connection if reload
        if self.client is not None:
            self.client.close()
        
        self.client = InfluxDBClient(url=self.complete_url, token=self.token, org=self.org)
        #self.client = InfluxDBClient(host=self.uri, port=self.port, database=self.db_name)
        # retrieve the org_id
        org_api = self.client.organizations_api()
        
        for org_response in  org_api.find_organizations():
            if org_response.name==self.org:
                self.org_id=org_response.id
        
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS) 

        try:
            self._ping_client()
        except ConnectionError:
            raise CantConnectToInfluxDB2Exception('connexion error')
         
        # Not sure we need to keep the buckeapi object longer than this
        bucket_api= self.client.buckets_api()
        if bucket_api.find_bucket_by_name(self.bucket)== None:
        #If we can't find the bucket, we create it.
            bucket_api.create_bucket(bucket_name=self.bucket, org_id=self.org_id)
     
        # We need the org_id in order to create a bucket
        #bucket_api.create_database(self.db_name, org_id="")
    # TO DO
    def save(self, report: Report, report_model: ReportModel):
        """
        Override from BaseDB

        :param report: Report to save
        :param report_model: ReportModel
        """
        ## Let's print the data to see its schema.
        #print("printing report")
        #print(report)
        #print("Printing serialized report")
        #print(report.serialize())
        data = report_model.to_influxdb(report.serialize())
        self.write_api.write(bucket= this.bucket, record= data)
        #self.client.write_points([data])
    # TO DO
    def save_many(self, reports: List[Report], report_model: ReportModel):
        """
        Save a batch of data

        :param reports: Batch of data.
        :param report_model: ReportModel
        """

        data_list = list(map(lambda r: report_model.to_influxdb(r.serialize()), reports))
        self.write_api.write(bucket= self.bucket, record= data_list)
