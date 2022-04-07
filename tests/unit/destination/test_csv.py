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
# Last modified : 7 April 2022

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

from powerapi.destination import CsvDestination
from powerapi.rx.formula import Formula
from powerapi.rx.report import Report
from powerapi.rx.source import BaseSource, source
from powerapi.rx.destination import Destination
from powerapi.exception import DestinationException

##############################
#
# Constants
#
##############################
GROUPS_CN = "groups"
SUB_GROUPS_L1_CN = "sub_group_l1"
SUB_GROUPS_L2_CN = "sub_group_l2"

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
                current_group_l2[current_column] = current_data.at[current_column]

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
# Tests
#
##############################


def test_error_file_not_found():
    """This test check that when the csv file don't exist an error is raised"""

    report_dict = {
        papi_report.TIMESTAMP_CN: datetime.now(),
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
    }

    the_source = FakeSource(create_fake_report_from_dict(report_dict))
    with pytest.raises(DestinationException):
        destination = CsvDestination("/tmp/powerapi/csv_test.csv")


# def test_destination_writing():
#     """This test only check if different method on source and destination  are called"""
#     # Setup
#     time = datetime.now()

#     report_dict = {
#         papi_report.TIMESTAMP_CN: time,
#         papi_report.SENSOR_CN: "test_sensor",
#         papi_report.TARGET_CN: "test_target",
#         papi_report.METADATA_CN: {
#             "scope": "cpu",
#             "socket": "0",
#             "formula": "RAPL_ENERGY_PKG",
#             "ratio": "1",
#             "predict": "0",
#             "power_units": "watt",
#         },
#         "groups": {
#             "core": {
#                 "0": {
#                     "0": {
#                         "CPU_CLK_THREAD_UNH": 2849918,
#                         "CPU_CLK_THREAD_UNH_": 49678,
#                         "time_enabled": 4273969,
#                         "time_running": 4273969,
#                         "LLC_MISES": 71307,
#                         "INSTRUCTIONS": 2673428,
#                     }
#                 }
#             }
#         },
#     }

#     the_source = FakeSource(create_fake_report_from_dict(report_dict))
#     destination = CsvDestination("/tmp/csv_test.csv")

#     # Exercise
#     source(the_source).subscribe(destination)
#     # Check Report has been writen
#     destination.on_completed()
#     f = open("/tmp/csv_test.csv", "r")
#     print(f.readline)
#     assert f.readline() == "timestamp,sensor,target\n"
#     assert f.readline() == str(time) + ",test_sensor,test_target\n"


def test_destination_full_report():
    """This test only check if different method on source and destination  are called"""
    # Setup
    time = datetime.now()

    report_dict = {
        papi_report.TIMESTAMP_CN: time,
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
        papi_report.METADATA_CN: {
            "scope": "cpu",
            "socket": "0",
            "formula": "RAPL_ENERGY_PKG",
            "ratio": 1,
            "predict": 0,
            "power_units": "watt",
        },
        "groups": {
            "core": {
                0: {
                    0: {
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

    the_source = FakeSource(create_fake_report_from_dict(report_dict))
    destination = CsvDestination("/tmp/csv_test.csv")

    # Exercise
    source(the_source).subscribe(destination)
    # Check Report has been writen
    destination.on_completed()
    f = open("/tmp/csv_test.csv", "r")
    assert (
        f.readline()
        == "timestamp,sensor,target,metadata:scope,metadata:socket,metadata:formula,metadata:ratio,metadata:predict,metadata:power_units,groups,sub_group_l1,sub_group_l2,CPU_CLK_THREAD_UNH,CPU_CLK_THREAD_UNH_,time_enabled,time_running,LLC_MISES,INSTRUCTIONS\n"
    )
    assert (
        f.readline()
        == str(time)
        + ",test_sensor,test_target,cpu,0,RAPL_ENERGY_PKG,1,0,watt,core,0,0,2849918,49678,4273969,4273969,71307,2673428\n"
    )


def test_csv_on_error():

    report_dict = {
        papi_report.TIMESTAMP_CN: datetime.now(),
        papi_report.SENSOR_CN: "test_sensor",
        papi_report.TARGET_CN: "test_target",
    }

    the_source = FakeBadSource(create_fake_report_from_dict(report_dict))
    destination = CsvDestination("/tmp/csv_test.csv")

    with pytest.raises(DestinationException):
        source(the_source).subscribe(destination)
