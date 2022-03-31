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
# Last modified : 23 March 2022

##############################
#
# Imports
#
##############################

from datetime import datetime
from typing import Dict

import pytest

from powerapi import quantity
from powerapi.exception import BadInputDataException

from powerapi.rx.power_report import create_power_report_from_dict, POWER_CN, PowerReport, \
    create_power_report_from_values
from powerapi.rx.report import Report, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX


##############################
#
# Fixtures
#
##############################

@pytest.fixture
def create_report_dict() -> Dict:
    return {
        TIMESTAMP_CN: datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 5.5 * quantity.W}


@pytest.fixture
def create_report_dict_with_metadata(create_report_dict) -> Dict:
    create_report_dict[METADATA_CN] = {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                                       "predict": 0,
                                       "power_units": "watt"}
    return create_report_dict


@pytest.fixture
def create_report_dict_with_data(create_report_dict_with_metadata) -> Dict:
    create_report_dict_with_metadata["groups"] = {"core":
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


##############################
#
# Tests
#
##############################


def test_of_create_power_report_from_dict(create_report_dict):
    """Test if a basic report is well-built"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = create_power_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, PowerReport)  # It is a power report
    assert len(report.index) == 1  # Only one index has to exist
    assert len(report.columns) == 1  # There a column with power data
    assert POWER_CN in report.columns
    assert len(report.index.names) == 3  # Only 3 names are used in the index


def test_of_create_power_report_from_values(create_report_dict):
    """Test if a basic report is well-built"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = create_power_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                             target=report_dict[TARGET_CN], power=report_dict[POWER_CN])

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, PowerReport)  # It is a power report
    assert len(report.index) == 1  # Only one index has to exist
    assert len(report.columns) == 1  # There a column with power data
    assert POWER_CN in report.columns
    assert len(report.index.names) == 3  # Only 3 names are used in the index


def test_of_create_power_report_from_dict_with_metadata(create_report_dict_with_metadata):
    """ Test that a power report with metadata is well-built"""

    # Setup

    report_dict = create_report_dict_with_metadata

    metadata = report_dict[METADATA_CN]

    # Exercise

    report = create_power_report_from_dict(report_dict)

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_of_create_power_report_from_values_with_metadata(create_report_dict_with_metadata):
    """ Test that a power report with metadata is well-built"""

    # Setup
    report_dict = create_report_dict_with_metadata
    metadata = report_dict[METADATA_CN]
    # Exercise

    report = create_power_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                             target=report_dict[TARGET_CN], power=report_dict[POWER_CN],
                                             metadata=metadata)

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_of_to_dict(create_report_dict):
    """Test if a power report is transformed correctly into a dict"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = create_power_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_of_to_dict_with_metadata(create_report_dict_with_metadata):
    """Test if a hwpc report with metadata is transformed correctly into a dict"""
    report_dict = create_report_dict_with_metadata

    # Exercise
    try:
        report = create_power_report_from_dict(report_dict)
        report_dict_to_check = report.to_dict()

        # Check that report is well-built
        assert report_dict_to_check == report_dict
    except BadInputDataException:
        assert False, "The report should be built"


def test_of_to_dict_with_data(create_report_dict_with_data):
    """Test if a hwpc report with data is transformed correctly into a dict"""

    # Setup
    report_dict = create_report_dict_with_data

    report_dict_expected = report_dict.copy()

    del (report_dict_expected["groups"])

    # Exercise
    report = create_power_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict_expected


def test_of_create_power_report_from_dict_fails_with_missing_power():
    """Test if a power report is not built when power value is missing"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
    }

    # Exercise
    report = None

    try:
        report = create_power_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with missing power value"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_power_report_from_dict_fails_with_missing_target(create_report_dict):
    """Test if a power report is not built when target value is missing"""

    # Setup
    report_dict = create_report_dict

    del (report_dict[TARGET_CN])

    report = None

    # Exercise

    try:
        report = create_power_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with missing target value"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_power_report_from_dict_fails_with_empty_dict():
    """Test if a power report is not built when report dict is empty"""

    # Setup
    report_dict = {}

    # Exercise
    report = None

    try:
        report = create_power_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with an empty dictionary as input"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None