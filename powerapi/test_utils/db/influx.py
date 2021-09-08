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
import pytest

from influxdb import InfluxDBClient


INFLUX_URI = 'localhost'
INFLUX_PORT = 8086
INFLUX_DBNAME = 'acceptation_test'


@pytest.fixture()
def influx_database(influxdb_content):
    """
    connect to a local influx database (localhost:8086) and store data contained in the list influxdb_content
    after test end, delete the data
    """
    client = InfluxDBClient(host=INFLUX_URI, port=INFLUX_PORT)
    _delete_db(client, INFLUX_DBNAME)
    _init_db(client, influxdb_content)
    yield client
    _delete_db(client, INFLUX_DBNAME)


def _init_db(client, content):

    if content != []:
        client.create_database(INFLUX_DBNAME)
        client.switch_database(INFLUX_DBNAME)
        client.write_points(content)


def _delete_db(client, db_name):
    client.drop_database(db_name)
    client.close()


def get_all_reports(client, db_name):
    """
    get all points stored in the database during test execution
    """
    client.switch_database(db_name)
    result = client.query('SELECT * FROM "power_consumption"')
    return list(result.get_points())
