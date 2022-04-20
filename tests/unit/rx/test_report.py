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

# Author : Daniel Romero Acero
# Last modified : 24 March 2022

##############################
#
# Imports
#
##############################
import time
from datetime import datetime
from typing import Dict, Any

import pytest
from numpy import int64, float64

from powerapi.exception import BadInputDataException
from powerapi.rx.report import Report, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX, TIME_CN, \
    TAGS_CN, DATE_FORMAT

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
# Fixtures
#
##############################

@pytest.fixture
def create_report_dict() -> Dict:
    """ Creates a report with basic info """
    return {
        TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT)+ '+00:00',  # We are 00 hours and 00 minutes ahead of UTC
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target"}


@pytest.fixture
def create_report_dict_with_metadata(create_report_dict) -> Dict:
    """ Creates a report dict with metadata and basic info """

    create_report_dict[METADATA_CN] = {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                                       "predict": 0,
                                       "power_units": "watt"}
    return create_report_dict


@pytest.fixture
def create_report_dict_with_data(create_report_dict_with_metadata) -> Dict:
    """ Creates a report dict with data """

    create_report_dict_with_metadata[GROUPS_CN] = {"core":
        {0:
            {0:
                {
                    "CPU_CLK_THREAD_UNH": 2849918,
                    "CPU_CLK_THREAD_UNH_": 49678,
                    "time_enabled": 4273969,
                    "time_running": 4273969,
                    "LLC_MISES": 71307,
                    "INSTRUCTIONS": 2673428},
                1:
                    {
                        "CPU_CLK_THREAD_UNH": 2849919,
                        "CPU_CLK_THREAD_UNH_": 49679,
                        "time_enabled": 4273970,
                        "time_running": 4273970,
                        "LLC_MISES": 71308,
                        "INSTRUCTIONS": 2673429}}}}
    return create_report_dict_with_metadata


@pytest.fixture
def create_influxdb_dict_with_metadata(create_report_dict_with_metadata) -> Dict:
    """ Creates the expected influx dict for a report """
    metadata = create_report_dict_with_metadata[METADATA_CN]
    metadata[SENSOR_CN] = create_report_dict_with_metadata[SENSOR_CN]
    metadata[TARGET_CN] = create_report_dict_with_metadata[TARGET_CN]

    return {TIME_CN: time.mktime(datetime.strptime(create_report_dict_with_metadata[TIMESTAMP_CN],
                                                   DATE_FORMAT).timetuple()),
            TAGS_CN: metadata}

##############################
#
# Classes
#
##############################

class SimpleReport(Report):
    """Simple Report for testing purposes"""

    def __init__(self, data: Dict, index_names: list, index_values: list) -> None:
        """ Creates a fake formula

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


def create_simple_report_from_dict(report_dic: Dict[str, Any]) -> SimpleReport:
    """ Creates a fake report by using the given information

        Args:
            report_dic: Dictionary that contains information of the report
    """

    # We get index names and values

    index_names, index_values, data = Report.get_index_information_and_data_from_report_dict(report_dic)

    data_by_columns = {}

    # We add the groups and their keys and sub keys as part of the index if it exists
    if GROUPS_CN in data.keys():
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
                    value_to_add = original_index_value + (key, key_level1, key_level2,)
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
    return SimpleReport(data_by_columns, index_names, index_values)


##############################
#
# Tests
#
##############################


def test_of_create_report_from_dict(create_report_dict):
    """Test if a basic report is well-built"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = Report.create_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, Report)  # It is a basic report
    assert len(report.index) == 1  # Only one index has to exist
    assert len(report.columns) == 0  # There is not data
    assert len(report.index.names) == 3  # Only 3 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names


def test_of_test_of_create_report_from_dict_with_metadata(create_report_dict_with_metadata):
    """ Test that a report with metadata is well-built"""

    # Setup
    report_dict = create_report_dict_with_metadata
    metadata = report_dict[METADATA_CN]

    # Exercise

    report = Report.create_report_from_dict(report_dict)

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_of_create_simple_report_from_dict_with_data(create_report_dict_with_data):
    """ Test that a report with data is well-built """
    report_dict = create_report_dict_with_data

    # Exercise

    report = create_simple_report_from_dict(report_dict)

    # Check that report is well-built

    data = report.loc[report.index[0]]

    assert data is not None
    assert len(data.index) == 6


def test_of_to_dict(create_report_dict):
    """Test if a basic report is transformed correctly into a dict"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = Report.create_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_of_to_dict_metadata(create_report_dict_with_metadata):
    """ Test if a basic report with metadata is transformed correctly into a dict """
    report_dict = create_report_dict_with_metadata

    # Exercise
    try:
        report = Report.create_report_from_dict(report_dict)
        report_dict_to_check = report.to_dict()

        # Check that report is well-built
        assert report_dict_to_check == report_dict
    except BadInputDataException:
        assert False, "The report should be built"


def test_of_to_dict_with_data(create_report_dict_with_data):
    """Test if a basic report with data is transformed correctly into a dict"""

    report_dict = create_report_dict_with_data

    # Exercise
    report = create_simple_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built

    assert report_dict_to_check == report_dict

    for _, metadata_val in report_dict_to_check[METADATA_CN].items():  # There is not numpy on the metadata
        assert not isinstance(metadata_val, int64)
        assert not isinstance(metadata_val, float64)


def test_of_create_report_from_dict_with_missing_target(create_report_dict):
    """Test if a report is not built with missing target value"""

    # Setup
    report_dict = create_report_dict
    del (report_dict[TARGET_CN])

    # Exercise
    report = None
    try:
        report = Report.create_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with missing target value"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_report_from_dict_with_missing_sensor(create_report_dict):
    """Test if a report is not built with missing sensor value"""

    # Setup
    report_dict = create_report_dict
    del (report_dict[SENSOR_CN])

    # Exercise
    report = None
    try:
        report = Report.create_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with missing sensor value"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_report_from_dict_with_missing_timestamp(create_report_dict):
    """Test if a report is not built with missing timestamp value"""

    # Setup
    report_dict = create_report_dict
    del (report_dict[TIMESTAMP_CN])

    # Exercise
    report = None
    try:
        report = Report.create_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with missing timestamp"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_report_from_dict_with_empty_dict():
    """Test if a report is not built with missing timestamp value"""

    # Setup
    report_dict = {}

    # Exercise
    report = None
    try:
        report = Report.create_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with an empty dictionary"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_to_influx_with_metadata(create_report_dict_with_metadata, create_influxdb_dict_with_metadata):
    """ Test that the to_influx works correctly when there is metadata """

    # Setup
    report = Report.create_report_from_dict(create_report_dict_with_metadata)
    influx_dict = create_influxdb_dict_with_metadata

    # Exercise
    influx_dic_to_check = report.to_influx()

    # Check that the influxdb dict is correctly built
    assert influx_dic_to_check == influx_dict
