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
# Last modified : 18 March 2022

##############################
#
# Imports
#
##############################

from datetime import datetime
from typing import Dict

import pytest
from numpy import int64, float64

from powerapi.exception import BadInputDataException
from powerapi.rx.hwpc_report import GROUPS_CN, HWPCReport
from powerapi.rx.report import TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX


##############################
#
# Fixtures
#
##############################

@pytest.fixture
def create_report_dict() -> Dict:
    return {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        GROUPS_CN:
            {"core":
                {"socket1":
                    {
                        "core0":
                            {
                                "CPU_CLK_THREAD_UNH": 2849918,
                                "CPU_CLK_THREAD_UNH_XX": 49678,
                                "time_enabled": 4273969,
                                "time_running": 4273969,
                                "LLC_MISES": 71307,
                                "INSTRUCTIONS": 2673428},
                        "core1":
                            {
                                "CPU_CLK_THREAD_UNH": 2849919,
                                "CPU_CLK_THREAD_UNH_XX": 49679,
                                "time_enabled": 4273970,
                                "time_running": 4273970,
                                "LLC_MISES": 71308,
                                "INSTRUCTIONS": 2673429}}}}}


@pytest.fixture
def create_report_with_empty_cells_dict() -> Dict:
    return {TIMESTAMP_CN: "2022-03-31T10:03:13.686Z",
            SENSOR_CN: "sensor",
            TARGET_CN: "all",
            GROUPS_CN: {
                "rapl":
                    {
                        "0":
                            {
                                "7":
                                    {
                                        "RAPL_ENERGY_PKG": 2151940096,
                                        "time_enabled": 503709618,
                                        "time_running": 503709618}}},
                "msr":
                    {
                        "0":
                            {
                                "0":
                                    {
                                        "mperf": 27131018,
                                        "aperf": 14511032,
                                        "TSC": 1062403542,
                                        "time_enabled": 503596227,
                                        "time_running": 503596227},
                                "1":
                                    {
                                        "mperf": 10724256,
                                        "aperf": 6219967,
                                        "TSC": 1062508538,
                                        "time_enabled": 503652347,
                                        "time_running": 503652347},
                                "2":
                                    {
                                        "mperf": 34843946,
                                        "aperf": 20517490,
                                        "TSC": 1062516244,
                                        "time_enabled": 503657311,
                                        "time_running": 503657311},
                                "3":
                                    {
                                        "mperf": 44880217,
                                        "aperf": 24521456,
                                        "TSC": 1061496242,
                                        "time_enabled": 503178189,
                                        "time_running": 503178189},
                                "4":
                                    {
                                        "mperf": 33798356,
                                        "aperf": 15466927,
                                        "TSC": 1061649272,
                                        "time_enabled": 503258869,
                                        "time_running": 503258869},
                                "5":
                                    {
                                        "mperf": 23821766,
                                        "aperf": 13564798,
                                        "TSC": 1061829320,
                                        "time_enabled": 503349457,
                                        "time_running": 503349457},
                                "6":
                                    {
                                        "mperf": 16511276,
                                        "aperf": 8192311,
                                        "TSC": 1061959760,
                                        "time_enabled": 503411582,
                                        "time_running": 503411582},
                                "7":
                                    {
                                        "mperf": 37457327,
                                        "aperf": 17288854,
                                        "TSC": 1062186326,
                                        "time_enabled": 503490955,
                                        "time_running": 503490955}}}}}


@pytest.fixture
def create_report_dict_with_metadata(create_report_dict) -> Dict:
    create_report_dict[METADATA_CN] = {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                                       "predict": 0,
                                       "power_units": "watt"}
    return create_report_dict


##############################
#
# Tests
#
##############################
def test_of_create_hwpc_report_from_dict(create_report_dict):
    """Test if a HWPC report is well-built"""

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = HWPCReport.create_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a hwpc report
    assert len(report.index) == 2  # 2 index have to exist
    assert len(report.columns) == 6  # There are 6 columns with groups data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert len(report.index.names) == 6  # Only 3 names are used in the index


def test_of_create_hwpc_report_with_empty_cells_from_dict(create_report_with_empty_cells_dict):
    """Test if a HWPC report is well-built"""

    # Setup
    report_dict = create_report_with_empty_cells_dict

    # Exercise
    report = HWPCReport.create_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a hwpc report
    assert len(report.index) == 9  # 9 index have to exist
    assert len(report.columns) == 6  # There are 6 columns with groups data
    assert "RAPL_ENERGY_PKG" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "mperf" in report.columns
    assert "aperf" in report.columns
    assert "TSC" in report.columns
    assert len(report.index.names) == 6  # Only 3 names are used in the index


def test_of_create_hwpc_report_from_dict_from_values(create_report_dict):
    """ Test if a HWPC Report is well-built """

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = HWPCReport.create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                                  target=report_dict[TARGET_CN], groups_dict=report_dict[GROUPS_CN])

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a hwpc report
    assert len(report.index) == 2  # Only one index has to exist
    assert len(report.columns) == 6  # There a column with power data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert len(report.index.names) == 6  # Only 6 names are used in the index


def test_of_create_hwpc_report_from_dict_with_metadata(create_report_dict_with_metadata):
    """ Test that a HWPC report with metadata is well-built """

    # Setup

    report_dict = create_report_dict_with_metadata
    metadata = report_dict[METADATA_CN]

    # Exercise

    report = HWPCReport.create_report_from_dict(report_dict)

    # Check that report is well-built, i.e., all the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_create_hwpc_report_from_dict_with_metadata_from_values(create_report_dict_with_metadata):
    """ Test that a power report with metadata is well-built """

    # Setup
    report_dict = create_report_dict_with_metadata
    metadata = report_dict[METADATA_CN]

    # Exercise

    report = HWPCReport.create_report_from_values(timestamp=report_dict[TIMESTAMP_CN], sensor=report_dict[SENSOR_CN],
                                            target=report_dict[TARGET_CN], metadata=report_dict[METADATA_CN],
                                            groups_dict=report_dict[GROUPS_CN])

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_of_to_dict(create_report_dict):
    """ Test if a hwpc report is transformed correctly into a dict """

    # Setup
    report_dict = create_report_dict

    # Exercise
    report = HWPCReport.create_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_of_to_dict_with_empty_cells_dict(create_report_with_empty_cells_dict):
    """ Test if a hwpc report is transformed correctly into a dict when there is missing cells """

    # Setup
    report_dict = create_report_with_empty_cells_dict

    # Exercise
    report = HWPCReport.create_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_to_dict_with_metadata(create_report_dict_with_metadata):
    """Test if a power report with metadata is transformed correctly into a dict"""
    report_dict = create_report_dict_with_metadata

    # Exercise
    report = HWPCReport.create_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict

    for _, group_dict in report_dict_to_check[GROUPS_CN].items():  # There is not numpy on the data
        for _, socket_dict in group_dict.items():
            for _, core_dict in socket_dict.items():
                for _, core_data in core_dict.items():
                    assert not isinstance(core_data, int64)
                    assert not isinstance(core_data, float64)


def test_of_create_hwpc_report_from_dict_with_missing_groups(create_report_dict):
    """Test if a hwpc report is not built when groups values are missing"""

    # Setup
    report_dict = create_report_dict
    del (report_dict[GROUPS_CN])

    # Exercise
    report = None

    try:
        report = HWPCReport.create_report_from_dict(report_dict)
        assert False, "create_hwpc_report_from_dict should not create a report with groups missing"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_hwpc_report_from_dict_with_missing_target(create_report_dict):
    """Test if a hwpc report is not built when target value is missing"""

    # Setup
    report_dict = create_report_dict
    del (report_dict[TARGET_CN])

    # Exercise
    report = None
    try:
        report = HWPCReport.create_report_from_dict(report_dict)
        assert False, "create_hwpc_report_from_dict should not create a report with missing target value"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None


def test_of_create_hwpc_report_from_dict_with_missing_wrong_groups(create_report_dict):
    """Test if a hwpc report is not built when groups values are missing"""

    # Setup

    report_dict = create_report_dict

    report_dict[GROUPS_CN] = " not a dict"

    # Exercise
    report = None
    try:
        report = HWPCReport.create_report_from_dict(report_dict)
        assert False, "create_hwpc_report_from_dict should not create a report with wrong groups type"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None
