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

# Author : Daniel  Romero Acero
# Last modified : 17 march 2022

##############################
#
# Imports
#
##############################

from typing import Dict, Any
from datetime import datetime

from powerapi.exception import BadInputDataException
from powerapi.rx.power_report import create_power_report_from_dict, POWER_CN, PowerReport
from powerapi.rx.report import Report, get_index_information_and_data_from_report_dict, \
    create_report_from_dict, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX

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

class FakeReport(Report):
    """Fake Report for testing purposes"""

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


##############################
#
# Tests
#
##############################


def test_building_of_simple_power_report():
    """Test if a basic report is well-built"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 5.5}

    # Exercise
    report = create_power_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, PowerReport)  # It is a power report
    assert len(report.index) == 1  # Only one index has to exist
    assert len(report.columns) == 0  # There is no data
    assert len(report.index.names) == 4  # Only 4 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names
    assert POWER_CN in report.index.names


def test_building_of_power_report_with_metadata():
    """ Test that a power report with metadata is well-built"""

    # Setup

    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"},
        POWER_CN: 55.5}
    metadata = report_dict[METADATA_CN]

    # Exercise

    report = create_power_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, Report)  # It is a basic report
    assert len(report.index) == 1  # Only one index has to exist
    assert len(report.columns) == 0  # There is no data
    assert len(report.index.names) == 10  # 10 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names
    assert POWER_CN in report.index.names

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_creation_of_dic_from_power_report():
    """Test if a basic report is transformed correctly into a dict"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 11}

    # Exercise
    report = create_power_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_creation_of_dic_from_power_report_with_metadata():
    """Test if a power report with metadata is transformed correctly into a dict"""
    report_dict = {
        POWER_CN: 11,
        TIMESTAMP_CN: datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"}}

    # Exercise
    try:
        report = create_power_report_from_dict(report_dict)
        report_dict_to_check = report.to_dict()

        # Check that report is well-built
        assert report_dict_to_check == report_dict
    except BadInputDataException:
        assert False, "The report should be built"


def test_creation_of_dict_from_report_with_data():
    """Test if a basic report with data is transformed correctly into a dict"""

    report_dict = {
        TIMESTAMP_CN: datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        POWER_CN: 11,
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"},
        "groups": {"core":
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
                            "INSTRUCTIONS": 2673429}}}}}

    report_dict_expected = {
        TIMESTAMP_CN: datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        POWER_CN: 11,
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"},
        }

    # Exercise
    report = create_power_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict_expected


def test_building_of_simple_power_report_fails_with_missing_values():
    """Test if a power report is not built when values are missing"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
    }

    report_dict_2 = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        POWER_CN: 11,
    }

    # Exercise
    report = None
    report_2 = None
    try:
        report = create_power_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with an incomplete dictionary"
    except BadInputDataException:
        pass

    try:
        report_2 = create_power_report_from_dict(report_dict_2)
        assert False, "create_report_from_dict should not create a report with an incomplete dictionary"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None
    assert report_2 is None
