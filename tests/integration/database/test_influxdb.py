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
import datetime
import pytest

from powerapi.database import InfluxDB, CantConnectToInfluxDBException
from powerapi.report import PowerReport, BadInputData
from powerapi.test_utils.db.influx import influx_database, get_all_reports, INFLUX_DBNAME, INFLUX_URI, INFLUX_PORT
from powerapi.test_utils.report.power import SENSOR_NAME, TARGET_NAME, gen_json_power_report

POWER_REPORT_0 = PowerReport(datetime.datetime.fromtimestamp(0), SENSOR_NAME,
                             TARGET_NAME, 100, {'socket': 0})
POWER_REPORT_1 = PowerReport(datetime.datetime.fromtimestamp(1), SENSOR_NAME,
                             TARGET_NAME, 100, {'socket': 0})
POWER_REPORT_2 = PowerReport(datetime.datetime.fromtimestamp(2), SENSOR_NAME,
                             TARGET_NAME, 100, {'socket': 0})


def define_influxdb_content(content):
    def wrap(func):
        setattr(func, '_influxdb_content', content)
        return func

    return wrap


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the influxdb_content fixtures in test environement with collected the
    value _influxdb_content if it exist or with an empty list

    :param metafunc: the test context given by pytest
    """
    if 'influxdb_content' in metafunc.fixturenames:
        content = getattr(metafunc.function, '_influxdb_content', None)
        if isinstance(content, list):
            metafunc.parametrize('influxdb_content', [content])
        else:
            metafunc.parametrize('influxdb_content', [[]])


@pytest.fixture()
def database():
    db = InfluxDB(PowerReport, INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME, ['socket'])
    yield db
    db.client.close()


####################
# CONNECTION TESTS #
####################
def test_correct_connection(influx_database, database):
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
    db = InfluxDB(PowerReport, 'tqldjslqskjd', INFLUX_PORT, INFLUX_DBNAME, ['socket'])
    with pytest.raises(CantConnectToInfluxDBException):
        db.connect()


def test_invalid_port_connection():
    """
    Try to connect the InfluxDB instance to an influxdb database with an invalid
    port

    Test if an CantConnectToInfluxDBException is raise
    """
    db = InfluxDB(PowerReport, INFLUX_URI, 1234, INFLUX_DBNAME, ['socket'])

    with pytest.raises(CantConnectToInfluxDBException):
        db.connect()


def test_database_initialisation(influx_database, database):
    """
    Connect an InfluxDB instance to an empty influxdb database

    test if the database specified to the InfluxDB instance was created
    """
    database.connect()

    assert_result = False

    for db in influx_database.get_list_database():
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


def test_write_one_report_in_empty_db(influx_database, database):
    """
    call the save method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_1)

    check_db_reports(influx_database, [POWER_REPORT_1])


def test_write_many_report_in_empty_db(influx_database, database):
    """
    call the save_many method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save_many([POWER_REPORT_1, POWER_REPORT_2])

    check_db_reports(influx_database, [POWER_REPORT_1, POWER_REPORT_2])


###############################
# REPORT WRITING NON EMPTY DB #
###############################
@define_influxdb_content(gen_json_power_report(1))
def test_write_one_report_in_non_empty_db(influx_database, database):
    """
    call the save method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_0)
    database.save(POWER_REPORT_1)
    check_db_reports(influx_database, [POWER_REPORT_0, POWER_REPORT_1])


@define_influxdb_content(gen_json_power_report(1))
def test_write_many_report_in_non_empty_db(influx_database, database):
    """
    call the save_many method with One PowerReport

    test if the report was writen in the database
    """
    database.connect()
    database.save(POWER_REPORT_0)
    database.save_many([POWER_REPORT_1, POWER_REPORT_2])

    check_db_reports(influx_database, [POWER_REPORT_0, POWER_REPORT_1, POWER_REPORT_2])
