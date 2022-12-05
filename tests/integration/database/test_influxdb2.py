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
import time

import pytest
from urllib3.exceptions import LocationValueError, NewConnectionError

from powerapi.database import InfluxDB, CantConnectToInfluxDBException
from powerapi.database.influxdb2 import InfluxDB2
from powerapi.report import PowerReport
from powerapi.test_utils.db.influx2 import INFLUX2_ORG, INFLUX2_TOKEN, INFLUX2_URL, INFLUX2_BUCKET_NAME, \
    influx_database, get_all_the_reports, INFLUX2_MEASUREMENT_NAME, INFLUX2_DEFAULT_START_DATE, INFLUX2_PORT, \
    INFLUX2_URL_WITHOUT_PORT
from powerapi.test_utils.report.power import SENSOR_NAME, TARGET_NAME, gen_json_power_report

POWER_REPORT_0 = PowerReport(datetime.datetime.fromisoformat('1970-01-01T00:00:00+00:00'), SENSOR_NAME,
                             TARGET_NAME, 100, {'socket': 0})
POWER_REPORT_1 = PowerReport(datetime.datetime.fromisoformat('1970-01-01T00:00:10+00:00'), SENSOR_NAME,
                             TARGET_NAME, 100, {'socket': 0})
POWER_REPORT_2 = PowerReport(datetime.datetime.now(datetime.timezone.utc), SENSOR_NAME,
                             TARGET_NAME, 200, {'socket': 0})

POWER_REPORT_3 = PowerReport(datetime.datetime.fromisoformat('2022-04-19T12:43:39.369+00:00'), SENSOR_NAME,
                             TARGET_NAME, 400, {'socket': 0})


@pytest.fixture()
def database():
    db = InfluxDB2(report_type=PowerReport, url=INFLUX2_URL, org=INFLUX2_ORG, bucket_name=INFLUX2_BUCKET_NAME,
                   token=INFLUX2_TOKEN, tags=['socket'])
    yield db
    db.client.close()


@pytest.fixture()
def database_with_port_connection():
    db = InfluxDB2(report_type=PowerReport, url=INFLUX2_URL_WITHOUT_PORT, org=INFLUX2_ORG,
                   bucket_name=INFLUX2_BUCKET_NAME,
                   token=INFLUX2_TOKEN, tags=['socket'], port=INFLUX2_PORT)
    yield db
    db.client.close()


####################
# CONNECTION TESTS #
####################
def test_correct_connection(database):
    """
    Connect the InfluxDB instance to an influxdb database

    Test if no exception was raised
    """
    database.connect()
    assert True


def test_correct_connection_with_port(database_with_port_connection):
    """
    Connect the InfluxDB instance to an influxdb database

    Test if no exception was raised
    """
    database_with_port_connection.connect()
    assert True


def test_invalid_url_connection():
    """
     Try to connect the InfluxDB instance to an influxdb database with an invalid
     uri

     Test if an CantConnectToInfluxDBException is raise
     """
    db = InfluxDB2(PowerReport, 'tqldjslqskjd', INFLUX2_ORG, INFLUX2_BUCKET_NAME, INFLUX2_TOKEN, ['socket'])
    with pytest.raises(BaseException):
        db.connect()


def test_invalid_url_connection_with_port():
    """
     Try to connect the InfluxDB instance to an influxdb database with an invalid
     uri

     Test if an CantConnectToInfluxDBException is raise
     """
    db = InfluxDB2(PowerReport, 'tqldjslqskjd', INFLUX2_ORG, INFLUX2_BUCKET_NAME, INFLUX2_TOKEN, ['socket'], 5555)
    with pytest.raises(BaseException):
        db.connect()


def test_invalid_port_connection():
    """
     Try to connect the InfluxDB instance to an influxdb database with an invalid
     port

     Test if an CantConnectToInfluxDBException is raise
     """
    db = InfluxDB2(PowerReport, 'http://localhost:1010', INFLUX2_ORG, INFLUX2_BUCKET_NAME, INFLUX2_TOKEN, ['socket'])

    with pytest.raises(BaseException):
        db.connect()


def test_database_initialisation(database):
    """
    Connect an InfluxDB instance to an empty influxdb database

    test if the database specified to the InfluxDB instance was created
    """
    database.connect()

    assert_result = database.get_db_by_name(INFLUX2_BUCKET_NAME) is not None

    assert assert_result


# ###########################
# # REPORT WRITING EMPTY DB #
# ###########################
def check_db_reports(client: InfluxDB2, input_reports):
    output_reports = get_all_the_reports(client, INFLUX2_DEFAULT_START_DATE, INFLUX2_BUCKET_NAME,
                                         INFLUX2_MEASUREMENT_NAME)

    assert len(output_reports[0].records) == len(input_reports)

    output_reports[0].records.sort(key=lambda r: r['_time'])
    input_reports.sort(key=lambda r: r.timestamp)

    for input_r, output_r in zip(input_reports, output_reports[0].records):
        # current_ouput_time = output_r['_time'].replace(tzinfo=None)
        assert output_r['sensor'] == input_r.sensor
        assert output_r['target'] == input_r.target
        assert output_r['_time'] == input_r.timestamp
        assert output_r['_value'] == input_r.power


def test_write_one_report_in_empty_db(influx_database, database):
    """
    call the save method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_1)

    check_db_reports(database, [POWER_REPORT_1])


def test_write_many_report_in_empty_db(influx_database, database):
    """
     call the save_many method with One PowerReport

     test if the report was writen in the database
     """
    database.connect()
    database.save_many([POWER_REPORT_1, POWER_REPORT_2, POWER_REPORT_3])

    check_db_reports(database, [POWER_REPORT_1, POWER_REPORT_2, POWER_REPORT_3])


# ###############################
# # REPORT WRITING NON EMPTY DB #
# ###############################

def test_write_one_report_in_non_empty_db(influx_database, database):
    """
     call the save method with One PowerReport

     test if the report was writen in the database
     """
    database.connect()
    database.save(POWER_REPORT_0)
    database.save(POWER_REPORT_1)
    check_db_reports(database, [POWER_REPORT_0, POWER_REPORT_1])


def test_write_many_report_in_non_empty_db(influx_database, database):
    """
     call the save_many method with One PowerReport

     test if the report was writen in the database
     """
    database.connect()
    database.save(POWER_REPORT_0)
    database.save_many([POWER_REPORT_1, POWER_REPORT_2])

    check_db_reports(database, [POWER_REPORT_0, POWER_REPORT_1, POWER_REPORT_2])
