# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
import datetime

import os

import pytest
from influxdb_client import InfluxDBClient

INFLUX2_ORG = 'org_test'
if os.environ.get('INFLUX2_ORG') is not None:
    INFLUX2_ORG = os.environ.get('INFLUX2_ORG')

INFLUX2_TOKEN = '1sdazvR2x9UE8eaLoVHhhcjGMu3Eje3_IkAp1zgIvFGQtSkcki--_BCePoicy3d35m1XNyrDXc15tRL-GCfkkA=='  # This token
if os.environ.get('INFLUX2_TOKEN') is not None:
    INFLUX2_TOKEN = os.environ.get('INFLUX2_TOKEN')

# has to be updated according to the local version
INFLUX2_URL = 'http://localhost:8086'
if os.environ.get('INFLUX2_URL') is not None:
    INFLUX2_URL = os.environ.get('INFLUX2_URL')


INFLUX2_URL_WITHOUT_PORT = 'http://localhost'
if os.environ.get('INFLUX2_URL_WITHOUT_PORT') is not None:
    INFLUX2_URL_WITHOUT_PORT = os.environ.get('INFLUX2_URL_WITHOUT_PORT')

INFLUX2_PORT = 8086
if os.environ.get('INFLUX2_PORT') is not None:
    INFLUX2_PORT = os.environ.get('INFLUX2_PORT')

INFLUX2_BUCKET_NAME = 'acceptation_test'
if os.environ.get('INFLUX2_BUCKET_NAME') is not None:
    INFLUX2_BUCKET_NAME = os.environ.get('INFLUX2_BUCKET_NAME')

INFLUX2_DEFAULT_START_DATE = '1970-01-01T00:00:00Z'

INFLUX2_MEASUREMENT_NAME = 'power_consumption'




@pytest.fixture()
def influx_database():
    """
        connect to a local influx database (localhost:8086) and store data contained in the list influxdb_content
        after test end, delete the data
    """
    print("Environment variables")

    print(os.environ)

    #if os.environ.get('INFLUX2_URL') is not None:
    #    INFLUX2_URL = os.environ.get('INFLUX2_URL')
    print('INFLUX2_URL zns..........;;')
    print(INFLUX2_URL)

    print('Token zns..........;;')
    print(INFLUX2_TOKEN)

    client = InfluxDBClient(url=INFLUX2_URL, token=INFLUX2_TOKEN, org=INFLUX2_ORG)

    _delete_bucket_content(client, INFLUX2_BUCKET_NAME)
    yield client
    _delete_bucket_content(client, INFLUX2_BUCKET_NAME)

    client.close()


def _delete_bucket_content(client: InfluxDBClient, bucket_name: str):
    """
        delete a bucket content

        :param client:  The client to work with the database
        :bucket_name:   The bucket to be deleted
    """

    delete_api = client.delete_api()
    delete_api.delete(bucket=bucket_name, start=INFLUX2_DEFAULT_START_DATE,
                      stop=datetime.datetime.now(datetime.timezone.utc),
                      predicate='_measurement="' + INFLUX2_MEASUREMENT_NAME + '"')


def get_all_the_reports(client: InfluxDBClient, start: str, bucket_name: str, measurement_name: str):
    """
        get all bucket measurement with the given name

        :param client:              The client to work with the database
        :param start:               The start date for filtering the measurements
        :param bucket_name:         The bucket for retrieving the measurements
        :param measurement_name     The measurement name
    """
    query = 'from(bucket:\"' + bucket_name + '\")' + \
            '|> range(start: ' + start + ')' \
                                         '|> filter(fn:(r) => r._measurement == \"' + measurement_name + '\")'

    return client.query_api.query(org=client.org, query=query)
