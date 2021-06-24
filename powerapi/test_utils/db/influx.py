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

import datetime

from influxdb import InfluxDBClient


def generate_power_report(sensor, target, timestamp):
    """ generate a power report with json format
    """

    return {
        'measurement': 'power_consumption',
        'tags': {'sensor': sensor,
                 'target': target},
        'time': str(datetime.datetime.fromtimestamp(timestamp)),
        'fields': {
            'power': 100
        }
    }


def create_empty_db(url, port):
    client = InfluxDBClient(host=url, port=port)
    client.ping()

    return client


def create_non_empty_db(url, port, db_name, number_of_reports, sensor_name, target_name):
    client = create_empty_db(url, port)
    client.create_database(db_name)
    client.switch_database(db_name)
    for i in range(number_of_reports):
        client.write_points([generate_power_report(sensor_name, target_name, i)])

    return client


def delete_db(client, db_name):
    client.drop_database(db_name)
    client.close()


def get_all_reports(client, db_name):
    client.switch_database(db_name)
    result = client.query('SELECT * FROM "power_consumption"')
    return list(result.get_points())
