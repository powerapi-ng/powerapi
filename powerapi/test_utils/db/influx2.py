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

import pytest
from influxdb_client import InfluxDBClient

INFLUX2_ORG = 'org_test'
INFLUX2_TOKEN = 'pTq179YXoLsAlpTDgF4PbaE8TmDx2ez8GVFgup5-4F7fc0EjfZs-eI6ZYWl66CJRxy5lwR0AE_VDeBDYIA9ATw==' # This token
# has to be updated according to the local version
INFLUX2_URL = 'http://localhost:8086'
INFLUX2_URL_WITHOUT_PORT = 'http://localhost'
INFLUX2_PORT = 8086
INFLUX2_BUCKET_NAME = 'acceptation_test'
INFLUX2_DEFAULT_START_DATE = '1970-01-01T00:00:00Z'
INFLUX2_MEASUREMENT_NAME = 'power_consumption'


@pytest.fixture()
def influx_database():
    """
        connect to a local influx database (localhost:8086) and store data contained in the list influxdb_content
        after test end, delete the data
    """
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
