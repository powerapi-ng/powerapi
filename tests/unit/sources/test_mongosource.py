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
# Last modified : 11 April 2022

##############################
#
# Imports
#
##############################

import powerapi.rx.report as papi_report
import pytest
from rx.core.typing import Observer, Scheduler
from typing import Optional, Dict, Any
from datetime import datetime
import pymongo
from powerapi.sources import MongoSource
from powerapi.rx.formula import Formula
from powerapi.rx.report import Report
from powerapi.rx.destination import Destination
from powerapi.exception import SourceException
from powerapi.rx.source import source

from powerapi.rx.power_report import (
    POWER_CN,
    PowerReport,
)
from powerapi.rx.report import (
    Report,
    TIMESTAMP_CN,
    SENSOR_CN,
    TARGET_CN,
    METADATA_CN,
    METADATA_PREFIX,
)

##############################
#
# Constants
#
##############################
GROUPS_CN = "groups"
SUB_GROUPS_L1_CN = "sub_group_l1"
SUB_GROUPS_L2_CN = "sub_group_l2"

MONGO_URI = "mongodb://localhost:27017/"
MONGO_INPUT_COLLECTION_NAME = "test_input"
MONGO_OUTPUT_COLLECTION_NAME = "test_output"
MONGO_DATABASE_NAME = "MongoDB1"

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

        new_report = papi_report.create_report_from_dict(report_dict)

        new_report["power"] = [report_dict["power"]]

        for observer in self.observers:
            observer.on_next(new_report)


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
        print(report)

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

    def to_dict(self) -> Dict:
        # We get the dictionary with the basic information
        report_dict = super().to_dict()

        # We have to create a dictionary for each group
        groups = {}
        groups_position = self.index.names.index(GROUPS_CN)
        subgroup_l1_position = self.index.names.index(SUB_GROUPS_L1_CN)
        subgroup_l2_position = self.index.names.index(SUB_GROUPS_L2_CN)

        for current_index in self.index:
            group_name = current_index[groups_position]
            current_group_l1_name = current_index[subgroup_l1_position]
            current_group_l2_name = current_index[subgroup_l2_position]

            # We create the group if required
            if group_name not in groups.keys():
                groups[group_name] = {}

            current_group = groups[group_name]

            # We create the group l1 if required
            if current_group_l1_name not in current_group.keys():
                current_group[current_group_l1_name] = {}

            current_group_l1 = current_group[current_group_l1_name]

            # We create the group l2 if required

            if current_group_l2_name not in current_group_l1.keys():
                current_group_l1[current_group_l2_name] = {}

            current_group_l2 = current_group_l1[current_group_l2_name]

            # We get the data related to the current group l2
            current_data = self.loc[current_index]

            for current_column in current_data.index:
                current_value = current_data.at[current_column]

                if isinstance(current_value, int64):
                    current_value = int(current_value)
                elif isinstance(current_value, float64):
                    current_value = float(current_value)

                current_group_l2[current_column] = current_value

        # We add the data, i.e., information that is not in the index
        report_dict[GROUPS_CN] = groups
        return report_dict


##############################
#
# Functions
#
##############################


def create_fake_report_from_dict(report_dic: Dict[str, Any]) -> FakeReport:
    """Creates a fake report by using the given information

    Args:
        report_dic: Dictionary that contains information of the report
    """

    # We get index names and values

    (
        index_names,
        index_values,
        data,
    ) = papi_report.get_index_information_and_data_from_report_dict(report_dic)

    data_by_columns = {}

    # We add the groups and their keys and sub keys as part of the index if it is exist
    if "groups" in data.keys():
        index_names.append(GROUPS_CN)
        index_names.append(SUB_GROUPS_L1_CN)
        index_names.append(SUB_GROUPS_L2_CN)
        groups = data[GROUPS_CN]

        # For each existing index_value, we have to add values related to groups' keys

        number_of_values_added = 0
        original_index_value = index_values[0]  # There is only one entry

        for key in groups.keys():

            # We add the group level values to the index

            # We add the sub_group_level1 values to the index
            sub_group_level1 = groups[key]

            for key_level1 in sub_group_level1.keys():

                # We add the sub_group_level2 values to the index
                sub_group_level2 = sub_group_level1[key_level1]

                # original_index_value_level2 = index_values[number_of_values_added]

                for key_level2 in sub_group_level2.keys():
                    value_to_add = original_index_value + (
                        key,
                        key_level1,
                        key_level2,
                    )
                    if number_of_values_added < len(index_values):
                        index_values[number_of_values_added] = value_to_add
                    else:
                        index_values.append(value_to_add)

                    number_of_values_added = number_of_values_added + 1

                    # We extract the data from the level2
                    data_values = sub_group_level2[key_level2]
                    for data_key in data_values:
                        current_value_to_add = data_values[data_key]
                        if data_key not in data_by_columns.keys():
                            data_by_columns[data_key] = [current_value_to_add]
                        else:
                            data_by_columns[data_key].append(current_value_to_add)

    # We create the report
    return FakeReport(data_by_columns, index_names, index_values)


##############################
#
# Tests utils function
#
##############################


@pytest.fixture
def mongo_database():
    """
    connect to a local mongo database (localhost:27017) and store data contained in the list influxdb_content
    after test end, delete the data
    """
    _gen_base_db_test(MONGO_URI)
    yield None
    _clean_base_db_test(MONGO_URI)


@pytest.fixture
def mongo_database_content():
    """
    connect to a local mongo database (localhost:27017) and store data contained in the list influxdb_content
    after test end, delete the data
    """

    time = datetime.now()

    report_dict = {
        papi_report.TIMESTAMP_CN: time,
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
        papi_report.METADATA_CN: {
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

    _gen_base_db_test(MONGO_URI, report_dict)
    yield None
    _clean_base_db_test(MONGO_URI)


def _gen_base_db_test(uri, content=None):
    mongo = pymongo.MongoClient(uri)
    db = mongo[MONGO_DATABASE_NAME]

    # delete collection if it already exist
    db[MONGO_INPUT_COLLECTION_NAME].drop()
    db.create_collection(MONGO_INPUT_COLLECTION_NAME)

    if content is not None:
        db[MONGO_INPUT_COLLECTION_NAME].insert_one(content)

    # delete output collection
    db[MONGO_OUTPUT_COLLECTION_NAME].drop()
    mongo.close()


def _clean_base_db_test(uri):
    """
    drop test_hwrep and test_result collections
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo[MONGO_DATABASE_NAME]
    db[MONGO_INPUT_COLLECTION_NAME].drop()
    db[MONGO_OUTPUT_COLLECTION_NAME].drop()
    mongo.close()


##############################
#
# Tests
#
##############################


def test_error_mongo_bad_url(mongo_database):
    """This test check that when the url is wring it raise an error"""

    report_dict = {
        papi_report.TIMESTAMP_CN: datetime.now(),
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
    }
    with pytest.raises(SourceException):
        the_source = MongoSource(papi_report, "mongodb://lel:27017/", "error", "error")


def test_error_mongo_bad_port(mongo_database):
    """This test check that when the port is wring it raise an error"""

    report_dict = {
        papi_report.TIMESTAMP_CN: datetime.now(),
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
    }

    with pytest.raises(SourceException):
        MongoSource(papi_report, "mongodb://localhost:1", "error", "error")


def test_mongodb_empty_db(mongo_database):
    """This test check that a report is well received"""

    time = datetime.now()

    report_dict = {
        papi_report.TIMESTAMP_CN: time,
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
        papi_report.METADATA_CN: {
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

    # Load DB
    mongodb = MongoSource(
        papi_report, MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME
    )
    the_destination = FakeDestination()

    source(mongodb).subscribe(the_destination)
    mongodb.close()
    # Check if the report is in the DB
    assert the_destination.report is None


def test_mongodb_read_basic_db(mongo_database_content):
    """This test check that a report is well received"""

    # Load DB
    mongodb = MongoSource(
        papi_report, MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME
    )
    the_destination = FakeDestination()

    # insert  report in db

    source(mongodb).subscribe(the_destination)
    mongodb.close()
    # Check if the report is in the DB
    assert the_destination.report is not None


# def test_mongodb_read_basic_db_with_quantity(mongo_database_quantity_content):
#     """This test check that a report is well received"""

#     # Load DB
#     mongodb = MongoSource(MONGO_URI, MONGO_DATABASE_NAME, MONGO_INPUT_COLLECTION_NAME)
#     the_destination = FakeDestination()

#     # insert  report in db

#     source(mongodb).subscribe(the_destination)
#     mongodb.close()
#     # Check if the report is in the DB
#     assert the_destination.report is not None
