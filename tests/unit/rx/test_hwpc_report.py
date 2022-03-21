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

from powerapi.exception import BadInputDataException
from powerapi.rx.hwpc_report import GROUPS_CN, create_hwpc_report_from_dict, HWPCReport, create_hwpc_report_from_values
from powerapi.rx.report import Report, TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN, METADATA_PREFIX


##############################
#
# Tests
#
##############################
def test_building_of_simple_hwpc_report_from_dict():
    """Test if a HWPC report is well-built"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        GROUPS_CN: {"core":
            {"socket1":
                {"core0":
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
                            "INSTRUCTIONS": 2673429}}}}

    }

    # Exercise
    report = create_hwpc_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a power report
    assert len(report.index) == 2  # Only one index has to exist
    assert len(report.columns) == 6  # There are 6 columns with groups data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert len(report.index.names) == 6  # Only 3 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names


def test_building_of_simple_hwpc_report_from_values():
    """Test if a HWPC Report is well-built"""

    # Setup
    timestamp = datetime.now()
    sensor = "test_sensor"
    target = "test_target"
    groups_dict = {"core":
        {"socket1":
            {0:
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
                        "INSTRUCTIONS": 2673429}}}}

    # Exercise
    report = create_hwpc_report_from_values(timestamp=timestamp, sensor=sensor, target=target, groups_dict=groups_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a power report
    assert len(report.index) == 2  # Only one index has to exist
    assert len(report.columns) == 6  # There a column with power data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert len(report.index.names) == 6  # Only 6 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names


def test_building_of_hwpc_report_with_metadata_from_dict():
    """ Test that a HWPC report with metadata is well-built"""

    # Setup

    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"},
        GROUPS_CN: {"core": {0:
                                 {0:
                                      {"CPU_CLK_THREAD_UNH": 2849918,
                                       "CPU_CLK_THREAD_UNH_XX": 49678,
                                       "time_enabled": 4273969,
                                       "time_running": 4273969,
                                       "LLC_MISES": 71307,
                                       "INSTRUCTIONS": 2673428},
                                  1:
                                      {
                                          "CPU_CLK_THREAD_UNH": 2849919,
                                          "CPU_CLK_THREAD_UNH_XX": 49679,
                                          "time_enabled": 4273970,
                                          "time_running": 4273970,
                                          "LLC_MISES": 71308,
                                          "INSTRUCTIONS": 2673429}},
                             1:
                                 {0:
                                     {
                                         "CPU_CLK_THREAD_UNH": 2849918,
                                         "CPU_CLK_THREAD_UNH_XX": 49678,
                                         "time_enabled": 4273969,
                                         "time_running": 4273969,
                                         "LLC_MISES": 71307,
                                         "INSTRUCTIONS": 2673428},
                                     1:
                                         {
                                             "CPU_CLK_THREAD_UNH": 2849919,
                                             "CPU_CLK_THREAD_UNH_XX": 49679,
                                             "time_enabled": 4273970,
                                             "time_running": 4273970,
                                             "LLC_MISES": 71308,
                                             "INSTRUCTIONS": 2673429}}}}}
    metadata = report_dict[METADATA_CN]

    # Exercise

    report = create_hwpc_report_from_dict(report_dict)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, HWPCReport)  # It is a HWPC report
    assert len(report.index) == 4  # Only one index has to exist
    assert len(report.columns) == 6  # There is a column with power data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert report.size == 24  # There is a size of 24 = 6 column * 4 rows
    assert len(report.index.names) == 12  # 12 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_building_of_hwpc_report_with_metadata_from_values():
    """ Test that a power report with metadata is well-built"""

    # Setup
    timestamp = datetime.now()
    sensor = "test_sensor"
    target = "test_target"
    metadata = {"scope": "cpu",
                "socket": "0",
                "formula": "RAPL_ENERGY_PKG",
                "ratio": 1,
                "predict": 0,
                "power_units": "watt"}
    groups = {"core": {0:
                           {0:
                                {"CPU_CLK_THREAD_UNH": 2849918,
                                 "CPU_CLK_THREAD_UNH_XX": 49678,
                                 "time_enabled": 4273969,
                                 "time_running": 4273969,
                                 "LLC_MISES": 71307,
                                 "INSTRUCTIONS": 2673428},
                            1:
                                {
                                    "CPU_CLK_THREAD_UNH": 2849919,
                                    "CPU_CLK_THREAD_UNH_XX": 49679,
                                    "time_enabled": 4273970,
                                    "time_running": 4273970,
                                    "LLC_MISES": 71308,
                                    "INSTRUCTIONS": 2673429}},
                       1:
                           {0:
                               {
                                   "CPU_CLK_THREAD_UNH": 2849918,
                                   "CPU_CLK_THREAD_UNH_XX": 49678,
                                   "time_enabled": 4273969,
                                   "time_running": 4273969,
                                   "LLC_MISES": 71307,
                                   "INSTRUCTIONS": 2673428},
                               1:
                                   {
                                       "CPU_CLK_THREAD_UNH": 2849919,
                                       "CPU_CLK_THREAD_UNH_XX": 49679,
                                       "time_enabled": 4273970,
                                       "time_running": 4273970,
                                       "LLC_MISES": 71308,
                                       "INSTRUCTIONS": 2673429}}}}

    # Exercise

    report = create_hwpc_report_from_values(timestamp=timestamp, sensor=sensor, target=target,
                                            metadata=metadata, groups_dict=groups)

    # Check that report is well-built
    assert report is not None
    assert isinstance(report, Report)  # It is a basic report
    assert len(report.index) == 4  # 4 index have to exist
    assert len(report.columns) == 6  # There is 6 columns with groups data
    assert "CPU_CLK_THREAD_UNH" in report.columns
    assert "CPU_CLK_THREAD_UNH_XX" in report.columns
    assert "time_enabled" in report.columns
    assert "time_running" in report.columns
    assert "LLC_MISES" in report.columns
    assert "INSTRUCTIONS" in report.columns
    assert report.size == 24  # There is a size of 24, 6 columns * 4 rows
    assert len(report.index.names) == 12  # 12 names are used in the index
    assert TIMESTAMP_CN in report.index.names
    assert SENSOR_CN in report.index.names
    assert TARGET_CN in report.index.names

    # All the metadata has to be included in the report as well as the values
    frame = report.index.to_frame(index=False)
    for key in metadata.keys():
        composed_key = METADATA_PREFIX + key
        assert composed_key in report.index.names
        value = frame.at[0, composed_key]
        assert value == metadata[key]


def test_creation_of_dict_from_hwpc_report():
    """Test if a basic report is transformed correctly into a dict"""

    # Setup
    report_dict = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        GROUPS_CN: {"core": {0:
                           {0:
                                {"CPU_CLK_THREAD_UNH": 2849918,
                                 "CPU_CLK_THREAD_UNH_XX": 49678,
                                 "time_enabled": 4273969,
                                 "time_running": 4273969,
                                 "LLC_MISES": 71307,
                                 "INSTRUCTIONS": 2673428},
                            1:
                                {
                                    "CPU_CLK_THREAD_UNH": 2849919,
                                    "CPU_CLK_THREAD_UNH_XX": 49679,
                                    "time_enabled": 4273970,
                                    "time_running": 4273970,
                                    "LLC_MISES": 71308,
                                    "INSTRUCTIONS": 2673429}},
                       1:
                           {0:
                               {
                                   "CPU_CLK_THREAD_UNH": 2849918,
                                   "CPU_CLK_THREAD_UNH_XX": 49678,
                                   "time_enabled": 4273969,
                                   "time_running": 4273969,
                                   "LLC_MISES": 71307,
                                   "INSTRUCTIONS": 2673428},
                               1:
                                   {
                                       "CPU_CLK_THREAD_UNH": 2849919,
                                       "CPU_CLK_THREAD_UNH_XX": 49679,
                                       "time_enabled": 4273970,
                                       "time_running": 4273970,
                                       "LLC_MISES": 71308,
                                       "INSTRUCTIONS": 2673429}}}}}

    # Exercise
    report = create_hwpc_report_from_dict(report_dict)
    report_dict_to_check = report.to_dict()

    # Check that report is well-built
    assert report_dict_to_check == report_dict


def test_creation_of_dict_from_hwpc_report_with_metadata():
    """Test if a power report with metadata is transformed correctly into a dict"""
    report_dict = {
        GROUPS_CN: {"core": {0:
                                 {0:
                                      {"CPU_CLK_THREAD_UNH": 2849918,
                                       "CPU_CLK_THREAD_UNH_XX": 49678,
                                       "time_enabled": 4273969,
                                       "time_running": 4273969,
                                       "LLC_MISES": 71307,
                                       "INSTRUCTIONS": 2673428},
                                  1:
                                      {
                                          "CPU_CLK_THREAD_UNH": 2849919,
                                          "CPU_CLK_THREAD_UNH_XX": 49679,
                                          "time_enabled": 4273970,
                                          "time_running": 4273970,
                                          "LLC_MISES": 71308,
                                          "INSTRUCTIONS": 2673429}},
                             1:
                                 {0:
                                     {
                                         "CPU_CLK_THREAD_UNH": 2849918,
                                         "CPU_CLK_THREAD_UNH_XX": 49678,
                                         "time_enabled": 4273969,
                                         "time_running": 4273969,
                                         "LLC_MISES": 71307,
                                         "INSTRUCTIONS": 2673428},
                                     1:
                                         {
                                             "CPU_CLK_THREAD_UNH": 2849919,
                                             "CPU_CLK_THREAD_UNH_XX": 49679,
                                             "time_enabled": 4273970,
                                             "time_running": 4273970,
                                             "LLC_MISES": 71308,
                                             "INSTRUCTIONS": 2673429}}}},
        TIMESTAMP_CN: datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                      "predict": 0,
                      "power_units": "watt"}}

    # Exercise
    try:
        report = create_hwpc_report_from_dict(report_dict)
        report_dict_to_check = report.to_dict()

        # Check that report is well-built
        assert report_dict_to_check == report_dict
    except BadInputDataException:
        assert False, "The report should be built"


def test_building_of_simple_hwpc_report_fails_with_missing_values():
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
        GROUPS_CN: {"core": {0:
                                 {0:
                                      {"CPU_CLK_THREAD_UNH": 2849918,
                                       "CPU_CLK_THREAD_UNH_XX": 49678,
                                       "time_enabled": 4273969,
                                       "time_running": 4273969,
                                       "LLC_MISES": 71307,
                                       "INSTRUCTIONS": 2673428},
                                  1:
                                      {
                                          "CPU_CLK_THREAD_UNH": 2849919,
                                          "CPU_CLK_THREAD_UNH_XX": 49679,
                                          "time_enabled": 4273970,
                                          "time_running": 4273970,
                                          "LLC_MISES": 71308,
                                          "INSTRUCTIONS": 2673429}},
                             1:
                                 {0:
                                     {
                                         "CPU_CLK_THREAD_UNH": 2849918,
                                         "CPU_CLK_THREAD_UNH_XX": 49678,
                                         "time_enabled": 4273969,
                                         "time_running": 4273969,
                                         "LLC_MISES": 71307,
                                         "INSTRUCTIONS": 2673428},
                                     1:
                                         {
                                             "CPU_CLK_THREAD_UNH": 2849919,
                                             "CPU_CLK_THREAD_UNH_XX": 49679,
                                             "time_enabled": 4273970,
                                             "time_running": 4273970,
                                             "LLC_MISES": 71308,
                                             "INSTRUCTIONS": 2673429}}}}
    }

    report_dict_3 = report_dict_2 = {
        TIMESTAMP_CN: datetime.now(),
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        GROUPS_CN: "not a dict"
    }
    # Exercise
    report = None
    report_2 = None
    report_3 = None
    try:
        report = create_hwpc_report_from_dict(report_dict)
        assert False, "create_hwpc_report_from_dict should not create a report with an incomplete dictionary"
    except BadInputDataException:
        pass

    try:
        report_2 = create_hwpc_report_from_dict(report_dict_2)
        assert False, "create_hwpc_report_from_dict should not create a report with an incomplete dictionary"
    except BadInputDataException:
        pass

    try:
        report_3 = create_hwpc_report_from_dict(report_dict_3)
        assert False, "create_hwpc_report_from_dict should not create a report with an incomplete dictionary"
    except BadInputDataException:
        pass

    # Check that report is not built
    assert report is None
    assert report_2 is None
    assert report_3 is None
