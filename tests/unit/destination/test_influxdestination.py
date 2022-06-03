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

# Author : Lauric Desauw
# Last modified : 1 June 2022

##############################
#
# Imports
#
##############################
import powerapi.rx.report as papi_report
import pytest
from influxdb import InfluxDBClient
from rx.core.typing import Observer, Scheduler
from typing import Optional, Dict, Any
from datetime import datetime
from numpy import int64, float64
from powerapi import quantity

from powerapi.destination import InfluxDestination
from powerapi.quantity import W
from powerapi.rx.formula import Formula
from powerapi.rx.report import Report
from powerapi.rx.source import BaseSource, source
from powerapi.rx.destination import Destination
from powerapi.rx.reports_group import ReportsGroup
from powerapi.exception import DestinationException


from powerapi.rx.reports_group import (
    TIMESTAMP_CN,
    SENSOR_CN,
    TARGET_CN,
    METADATA_CN,
)

##############################
#
# Constants
#
##############################
GROUPS_CN = "groups"
SUB_GROUPS_L1_CN = "sub_group_l1"
SUB_GROUPS_L2_CN = "sub_group_l2"

INFLUX_URI = "localhost"
INFLUX_PORT = 8086
INFLUX_DBNAME = "unit_test"


GROUPS_CN = "groups"
SOCKET_CN = "socket_id"
CORE_CN = "core_id"
EVENT_CN = "event_id"
EVENT_VALUE_CN = "event_value"
POWER_CN = "power"
##############################
#
# Classes
#
##############################


class FakeFormula(Formula):
    """Fake formula for testing the base class"""

    def __init__(self) -> None:
        """Creates a fake formula

        Args:

        """
        super().__init__()

    def process_report(self, report: Report):
        """Required method for processing data as an observer of a source

        Args:
        report: The operator (e.g. a destination) that will process the output of the formula
        """

        report_dict = {
            "timestamp": "2022-02-21T14:53:50.152Z",
            "sensor": "sensor",
            "target": "cool_noyce",
            "metadata": {
                "scope": "cpu",
                "socket": "0",
                "formula": "624236cabf67b95a8dd714529b91c19f162ab94d",
                "ratio": 1,
                "predict": 164.9913654183235,
                "power_units": "watt",
            },
            "power": 164.9913654183235,
        }

        new_report = create_report_from_dict(report_dict)

        new_report["power"] = [report_dict["power"]]

        for observer in self.observers:
            observer.on_next(new_report)


class FakeSource(BaseSource):
    """Fake source for testing purposes"""

    def __init__(self, report: Report) -> None:
        """Creates a fake source

        Args:

        """
        super().__init__()
        self.report = report

    def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
        """Required method for retrieving data from a source by a Formula

        Args:
            operator: The operator (e.g. a formula or log)  that will process the data
            scheduler: Used for parallelism. Not used for the time being

        """
        operator.on_next(self.report)

    def close(self):
        """Closes the access to the data source"""
        pass


class FakeBadSource(BaseSource):
    """Fake source for testing purposes"""

    def __init__(self, report: Report) -> None:
        """Creates a fake source

        Args:

        """
        super().__init__()
        self.report = report

    def subscribe(self, operator: Observer, scheduler: Optional[Scheduler] = None):
        """Required method for retrieving data from a source by a Formula

        Args:
            operator: The operator (e.g. a formula or log)  that will process the data
            scheduler: Used for parallelism. Not used for the time being

        """
        operator.on_error(ValueError)

    def close(self):
        """Closes the access to the data source"""
        pass


class FakeDestination(Destination):
    """Fake destination for testing purposes"""

    def __init__(self) -> None:
        """Creates a fake source

        Args:

        """
        super().__init__()
        self.report = None

    def store_report(self, report):
        """Required method for storing a report

        Args:
            report: The report that will be stored
        """
        self.report = report

    def on_completed(self) -> None:
        pass

    def on_error(self, error: Exception) -> None:
        pass

    # def on_next(self, report):
    #    self.store_report(report)


class FakeReport(Report):
    """Fake Report for testing purposes"""

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """Creates a fake formula

        Args:

        """
        super().__init__(data=data, index_names=index_names, index_values=index_values)
        self.is_test = True
        self.processed = False

    def to_influx(self):
        return {
            "measurement": "measure_name",
            "time": 0,
            "tags": {"units": W},
            "fields": {"test": 0.0},
        }


class FakeQuantityReport(Report):
    """Fake Report for testing purposes"""

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """Creates a fake formula

        Args:

        """
        super().__init__(data=data, index_names=index_names, index_values=index_values)
        self.is_test = True
        self.processed = False

    def to_influx(self):
        return {
            "measurement": "measure_name_q",
            "time": 0,
            "tags": {"units": W},
            "fields": {"test": 0.0},
        }

    ##############################
    #
    # Functions
    #
    ##############################


def create_reports_group_from_dicts(reports_dict: [Dict[str, Any]]):
    """Creates a group report by using the given information

    All the dictionaries have the same timestamp, sensor and metadata
    Args:
        reports_dict: List of dictionaries that contains information of the report
    Return :
        A new group report created using information contained in the list of dictionaries
    """
    # We check that all the required information is in the input dictionary

    # We create the report
    report_data_dict = {
        TARGET_CN: [],
        GROUPS_CN: [],
        SOCKET_CN: [],
        CORE_CN: [],
        EVENT_CN: [],
        EVENT_VALUE_CN: [],
    }
    for current_report_dict in reports_dict:
        current_groups_dict = current_report_dict[GROUPS_CN]
        current_target = current_report_dict[TARGET_CN]
        for current_group_id, current_sockets_dict in current_groups_dict.items():
            for (
                current_socket_id,
                current_cores_dict,
            ) in current_sockets_dict.items():
                for (
                    current_core_id,
                    current_events_dict,
                ) in current_cores_dict.items():
                    for (
                        current_event_id,
                        current_event_value,
                    ) in current_events_dict.items():
                        # We add a line for each event value
                        report_data_dict[TARGET_CN].append(current_target)
                        report_data_dict[GROUPS_CN].append(current_group_id)
                        report_data_dict[SOCKET_CN].append(current_socket_id)
                        report_data_dict[CORE_CN].append(current_core_id)
                        report_data_dict[EVENT_CN].append(current_event_id)
                        report_data_dict[EVENT_VALUE_CN].append(current_event_value)

    report = Report(data=report_data_dict)

    # We get the basic infos from the first entry of the list
    current_report_dict = reports_dict[0]
    metadata = (
        {}
        if METADATA_CN not in current_report_dict.keys()
        else current_report_dict[METADATA_CN]
    )
    return ReportsGroup(
        timestamp=current_report_dict[TIMESTAMP_CN],
        sensor=current_report_dict[SENSOR_CN],
        metadata=metadata,
        report=report,
    )


##############################
#
# Tests utils function
#
##############################


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the influxdb_content fixtures in test environement with collected the
    value _influxdb_content if it exist or with an empty list

    :param metafunc: the test context given by pytest
    """
    if "influxdb_content" in metafunc.fixturenames:
        content = getattr(metafunc.function, "_influxdb_content", None)
        if isinstance(content, list):
            metafunc.parametrize("influxdb_content", [content])
        else:
            metafunc.parametrize("influxdb_content", [[]])


@pytest.fixture()
def influx_database(influxdb_content):
    """
    connect to a local influx database (localhost:8086) and store data contained in the list influxdb_content
    after test end, delete the data
    """
    client = InfluxDBClient(host=INFLUX_URI, port=INFLUX_PORT)
    # _delete_db(client, INFLUX_DBNAME)
    _init_db(client, influxdb_content)
    yield client
    # _delete_db(client, INFLUX_DBNAME)


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
    result = client.query("SELECT * FROM measure_name")
    return list(result.get_points())


##############################
#
# Tests
#
##############################


def test_error_influx_bad_url(influx_database):
    """This test check that when the url is wring it raise an error"""

    time = datetime.now()

    report_dict = {
        TIMESTAMP_CN: time,
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {
            "scope": "cpu",
            "socket": "0",
            "formula": "RAPL_ENERGY_PKG",
            "ratio": "1",
            "predict": "0",
            "power_units": "watt",
        },
        "groups": {
            "core": {
                "0": {
                    "0": {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428,
                    }
                }
            }
        },
    }

    the_source = FakeSource(create_reports_group_from_dicts([report_dict]))
    with pytest.raises(DestinationException):
        InfluxDestination("lochst", "10", "10")


def test_error_influx_bad_port(influx_database):
    """This test check that when the port is wring it raise an error"""

    time = datetime.now()

    report_dict = {
        TIMESTAMP_CN: time,
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {
            "scope": "cpu",
            "socket": "0",
            "formula": "RAPL_ENERGY_PKG",
            "ratio": "1",
            "predict": "0",
            "power_units": "watt",
        },
        "groups": {
            "core": {
                "0": {
                    "0": {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428,
                    }
                }
            }
        },
    }

    the_source = FakeSource(create_reports_group_from_dicts([report_dict]))
    with pytest.raises(DestinationException):
        InfluxDestination("influxdb://localhost", "error", "error")


def test_influxdb_read_basic_db(influx_database):
    """This test check that a report is well writen in the mogodb"""

    time = datetime.now()

    report_dict = {
        TIMESTAMP_CN: time,
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {
            "scope": "cpu",
            "socket": "0",
            "formula": "RAPL_ENERGY_PKG",
            "ratio": "1",
            "predict": "0",
            "power_units": "watt",
        },
        "groups": {
            "core": {
                "0": {
                    "0": {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428,
                    }
                }
            }
        },
    }

    the_source = FakeSource(create_reports_group_from_dicts([report_dict]))

    # Load DB
    influx = InfluxDestination(INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME)

    source(the_source).subscribe(influx)

    # Check if the report is in the DB

    print(influx.client.write_points([report_dict]))

    influx.client.switch_database(INFLUX_DBNAME)
    result = influx.client.query("SELECT * FROM measure_name ")
    output_reports = list(result.get_points())

    assert len(output_reports) == 1


def test_influxdb_on_error(influx_database):

    time = datetime.now()

    report_dict = {
        TIMESTAMP_CN: time.strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        "groups": {
            "core": {
                "0": {
                    "0": {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428,
                    }
                }
            }
        },
    }

    the_source = FakeBadSource(create_reports_group_from_dicts([report_dict]))

    influx = InfluxDestination(INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME)
    with pytest.raises(DestinationException):
        source(the_source).subscribe(influx)


def test_influxdb_read_quantity(influx_database):
    """This test check that a report is well writen in the mogodb"""

    time = datetime.now()

    report_dict = {
        TIMESTAMP_CN: time.strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 5.5 * quantity.W,
        "groups": {
            "core": {
                "0": {
                    "0": {
                        "CPU_CLK_THREAD_UNH": 2849918,
                        "CPU_CLK_THREAD_UNH_": 49678,
                        "time_enabled": 4273969,
                        "time_running": 4273969,
                        "LLC_MISES": 71307,
                        "INSTRUCTIONS": 2673428,
                    }
                }
            }
        },
    }

    the_source = FakeSource(create_reports_group_from_dicts([report_dict]))
    influx = InfluxDestination(INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME)

    source(the_source).subscribe(influx)

    # Check if the report is in the DB

    influx.client.switch_database(INFLUX_DBNAME)
    result = influx.client.query("SELECT * FROM measure_name_q ")
    output_reports = list(result.get_points())

    assert len(output_reports) == 1
