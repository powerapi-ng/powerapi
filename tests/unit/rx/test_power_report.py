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
import time
from datetime import datetime
from typing import Dict

import pytest

from powerapi import quantity
from powerapi.exception import BadInputDataException

from powerapi.rx.power_report import POWER_CN, PowerReport, \
    MEASUREMENT_NAME, UNIT_CN
from powerapi.rx.report import TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX, TIME_CN, \
    TAGS_CN, FIELDS_CN, MEASUREMENT_CN, DATE_FORMAT


##############################
#
# Fixtures
#
##############################

@pytest.fixture
def create_report_dict() -> Dict:
    """ Creates a report with basic info """

    return {
        TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 5.5 * quantity.W}


@pytest.fixture
def create_report_dict_with_metadata(create_report_dict) -> Dict:
    """ Creates a report with metadata and basic information """

    create_report_dict[METADATA_CN] = {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                                       "predict": 0}
    return create_report_dict


@pytest.fixture
def create_report_dict_with_data(create_report_dict_with_metadata) -> Dict:
    """ Creates a report with data """

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


@pytest.fixture
def create_influxdb_dict_with_metadata(create_report_dict_with_metadata) -> Dict:
    """ Creates the expected influx dict for a report """

    metadata = create_report_dict_with_metadata[METADATA_CN]
    metadata[SENSOR_CN] = create_report_dict_with_metadata[SENSOR_CN]
    metadata[TARGET_CN] = create_report_dict_with_metadata[TARGET_CN]
    metadata[UNIT_CN] = str(create_report_dict_with_metadata[POWER_CN].units)

    return {TIME_CN: time.mktime(datetime.strptime(create_report_dict_with_metadata[TIMESTAMP_CN],
                                                   DATE_FORMAT).timetuple()),
            TAGS_CN: metadata,
            FIELDS_CN: {POWER_CN: create_report_dict_with_metadata[POWER_CN].magnitude},
            MEASUREMENT_CN: MEASUREMENT_NAME}


@pytest.fixture
def create_influxdb_dict(create_report_dict) -> Dict:
    """ Creates the expected influx dict for a report """

    return {TIME_CN: time.mktime(datetime.strptime(create_report_dict[TIMESTAMP_CN],
                                                   DATE_FORMAT).timetuple()),
            TAGS_CN: {UNIT_CN: str(create_report_dict[POWER_CN].units),
                      SENSOR_CN:create_report_dict[SENSOR_CN],
                      TARGET_CN:create_report_dict[TARGET_CN]},
            FIELDS_CN: {POWER_CN: create_report_dict[POWER_CN].magnitude},
            MEASUREMENT_CN: MEASUREMENT_NAME}


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
    report = PowerReport.create_report_from_dict(report_dict)

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
    report = PowerReport.create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
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

    report = PowerReport.create_report_from_dict(report_dict)

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

    report = PowerReport.create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
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
    report = PowerReport.create_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_of_to_dict_with_metadata(create_report_dict_with_metadata):
    """Test if a hwpc report with metadata is transformed correctly into a dict"""
    report_dict = create_report_dict_with_metadata

    # Exercise
    try:
        report = PowerReport.create_report_from_dict(report_dict)
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
    report = PowerReport.create_report_from_dict(report_dict)
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
        report = PowerReport.create_report_from_dict(report_dict)
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
        report = PowerReport.create_report_from_dict(report_dict)
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
        report = PowerReport.create_report_from_dict(report_dict)
        assert False, "create_report_from_dict should not create a report with an empty dictionary as input"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_to_influx(create_report_dict, create_influxdb_dict):
    """ Test that the to_influx works correctly when there is metadata """

    # Setup
    report = PowerReport.create_report_from_dict(create_report_dict)
    influx_dict = create_influxdb_dict

    # Exercise
    influx_dic_to_check = report.to_influx()

    print(influx_dic_to_check)
    # Check that the influxdb dict is correctly built
    assert influx_dic_to_check == influx_dict


def test_of_to_influx_with_metadata(create_report_dict_with_metadata, create_influxdb_dict_with_metadata):
    """ Test that the to_influx works correctly when there is metadata """

    # Setup
    report = PowerReport.create_report_from_dict(create_report_dict_with_metadata)
    influx_dict = create_influxdb_dict_with_metadata

    # Exercise
    influx_dic_to_check = report.to_influx()

    print(influx_dic_to_check)
    # Check that the influxdb dict is correctly built
    assert influx_dic_to_check == influx_dict
