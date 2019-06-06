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
import pytest

from powerapi.database import InfluxDB, CantConnectToInfluxDBException
from powerapi.report_model import PowerModel, BadInputData
from powerapi.report import PowerReport
from tests.influx_utils import generate_power_report, create_empty_db
from tests.influx_utils import create_non_empty_db, delete_db, get_all_reports


INFLUX_URI = 'localhost'
INFLUX_PORT = 8086
INFLUX_DBNAME = 'unit_test'

SENSOR_NAME = 'sensor_test'
TARGET_NAME = 'target_test'

POWER_REPORT_0 = PowerReport(datetime.datetime.fromtimestamp(0), SENSOR_NAME,
                             TARGET_NAME, 100, {})
POWER_REPORT_1 = PowerReport(datetime.datetime.fromtimestamp(1), SENSOR_NAME,
                             TARGET_NAME, 100, {})
POWER_REPORT_2 = PowerReport(datetime.datetime.fromtimestamp(2), SENSOR_NAME,
                             TARGET_NAME, 100, {})


def bad_serialize():
    return {
        'measurement': 'power_consumption',
        'tags': {'target': TARGET_NAME},
        'time': str(datetime.datetime.fromtimestamp(100)),
        'fields': {
            'power': 100
        }}


BAD_POWER_REPORT = PowerReport(datetime.datetime.fromtimestamp(2), SENSOR_NAME, TARGET_NAME, 100, {})
BAD_POWER_REPORT.serialize = bad_serialize


@pytest.fixture()
def init_empty_database():
    client = create_empty_db(INFLUX_URI, INFLUX_PORT)
    yield client
    delete_db(client, INFLUX_DBNAME)


@pytest.fixture()
def init_database_with_one_report():
    client = create_non_empty_db(INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME, 1,
                                 SENSOR_NAME, TARGET_NAME)
    yield client
    delete_db(client, INFLUX_DBNAME)


@pytest.fixture()
def database():
    db = InfluxDB(INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME)

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


def test_invalid_uri_connection():
    """
    Try to connect the InfluxDB instance to an influxdb database with an invalid
    uri

    Test if an CantConnectToInfluxDBException is raise
    """
    db = InfluxDB('tqldjslqskjd', INFLUX_PORT, INFLUX_DBNAME)
    with pytest.raises(CantConnectToInfluxDBException):
        db.connect()



def test_invalid_port_connection():
    """
    Try to connect the InfluxDB instance to an influxdb database with an invalid
    port

    Test if an CantConnectToInfluxDBException is raise
    """
    db = InfluxDB(INFLUX_URI, 1234, INFLUX_DBNAME)

    with pytest.raises(CantConnectToInfluxDBException):
        db.connect()


def test_database_initialisation(init_empty_database, database):
    """
    Connect an InfluxDB instance to an empty influxdb database

    test if the database specified to the InfluxDB instance was created
    """
    database.connect()

    assert_result = False

    for db in init_empty_database.get_list_database():
        if db['name'] == INFLUX_DBNAME:
            assert_result = True
    assert assert_result


###########################
# REPORT WRITING EMPTY DB #
###########################
def check_db_reports(client, input_reports):
    output_reports = get_all_reports(client, INFLUX_DBNAME)

    assert len(output_reports) == len(input_reports)

    output_reports.sort(key=lambda r: r['time'])
    input_reports.sort(key=lambda r: r.timestamp)

    for input_r, output_r in zip(input_reports, output_reports):
        assert input_r.sensor == output_r['sensor']
        assert input_r.target == output_r['target']
        assert input_r.timestamp == datetime.datetime.strptime(output_r['time'], '%Y-%m-%dT%H:%M:%SZ')
        assert input_r.power == output_r['power']


def test_write_one_bad_report_in_empty_db(init_empty_database, database):
    """
    call the save method with One PowerReport with no sensor field

    test if a BadInputData is raise and the database is still empty
    """
    database.connect()
    with pytest.raises(BadInputData):
        database.save(BAD_POWER_REPORT, PowerModel())

    assert get_all_reports(init_empty_database, INFLUX_DBNAME) == []


def test_write_one_report_in_empty_db(init_empty_database, database):
    """
    call the save method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_1, PowerModel())

    check_db_reports(init_empty_database, [POWER_REPORT_1])


def test_write_many_report_in_empty_db(init_empty_database, database):
    """
    call the save_many method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save_many([POWER_REPORT_1, POWER_REPORT_2], PowerModel())

    check_db_reports(init_empty_database, [POWER_REPORT_1, POWER_REPORT_2])


def test_one_good_one_bad_reports_in_empty_db(init_empty_database, database):
    """
    call the save_many method on a list composed with one good formated power
    report and one bad formated power report (missing sensor field)

    test if a BadInputData is raise and the database is still empty

    """
    database.connect()
    with pytest.raises(BadInputData):
        database.save_many([POWER_REPORT_1, BAD_POWER_REPORT], PowerModel())
    assert get_all_reports(init_empty_database, INFLUX_DBNAME) == []


###############################
# REPORT WRITING NON EMPTY DB #
###############################
def test_write_one_bad_report_in_non_empty_db(init_database_with_one_report, database):
    """
    call the save method with One PowerReport with no sensor field

    test if a BadInputData is raise and the database is still empty
    """
    database.connect()
    with pytest.raises(BadInputData):
        database.save(BAD_POWER_REPORT, PowerModel())

    check_db_reports(init_database_with_one_report, [POWER_REPORT_0])


def test_write_one_report_in_non_empty_db(init_database_with_one_report, database):
    """
    call the save method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_1, PowerModel())

    check_db_reports(init_database_with_one_report, [POWER_REPORT_0, POWER_REPORT_1])


def test_write_many_report_in_non_empty_db(init_database_with_one_report, database):
    """
    call the save_many method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save_many([POWER_REPORT_1, POWER_REPORT_2], PowerModel())

    check_db_reports(init_database_with_one_report, [POWER_REPORT_0, POWER_REPORT_1, POWER_REPORT_2])


def test_one_good_one_bad_reports_in_non_empty_db(init_database_with_one_report, database):
    """
    call the save_many method on a list composed with one good formated power
    report and one bad formated power report (missing sensor field)

    test if a BadInputData is raise and the database is still empty

    """
    database.connect()
    with pytest.raises(BadInputData):
        database.save_many([POWER_REPORT_1, BAD_POWER_REPORT], PowerModel())
    check_db_reports(init_database_with_one_report, [POWER_REPORT_0])
