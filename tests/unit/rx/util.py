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
# Last modified : 17 May 2022

##############################
#
# Imports
#
##############################
from datetime import datetime

import pytest

from typing import Dict, Any

from powerapi import quantity
from powerapi.rx.hwpc_reports_group import SOCKET_CN, GROUPS_CN, CORE_CN, EVENT_CN, EVENT_VALUE_CN, MSR_GROUP, \
    CORE_GROUP
from powerapi.rx.power_reports_group import POWER_CN, UNIT_CN, MEASUREMENT_NAME
from powerapi.rx.report import TARGET_CN
from powerapi.rx.reports_group import TIMESTAMP_CN, SENSOR_CN, METADATA_CN, DATE_FORMAT, TIME_CN, TAGS_CN, \
    FIELDS_CN, MEASUREMENT_CN, ReportsGroup, GENERIC_MEASUREMENT_NAME


##############################
#
# Fixtures
#
##############################

@pytest.fixture
def create_report_dict() -> Dict:
    """ Creates a report with basic info """
    return {
        TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT) + '+00:00',  # We are 00 hours and 00 minutes ahead of UTC
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target"}


@pytest.fixture
def create_wrong_report_dict() -> Dict:
    """ Creates a report with missing info """
    return {
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
def create_influxdb_dict(create_report_dict) -> Dict:
    """ Creates the expected influx dict for a report """

    return {TIME_CN: create_report_dict[TIMESTAMP_CN],
            TAGS_CN: {SENSOR_CN: create_report_dict[SENSOR_CN],
                      TARGET_CN: create_report_dict[TARGET_CN]},
            MEASUREMENT_CN: GENERIC_MEASUREMENT_NAME}


@pytest.fixture
def create_influxdb_dict_with_metadata(create_report_dict_with_metadata) -> Dict:
    """ Creates the expected influx dict for a report """
    metadata = create_report_dict_with_metadata[METADATA_CN]
    metadata[SENSOR_CN] = create_report_dict_with_metadata[SENSOR_CN]
    metadata[TARGET_CN] = create_report_dict_with_metadata[TARGET_CN]

    return {TIME_CN: create_report_dict_with_metadata[TIMESTAMP_CN],
            TAGS_CN: metadata}


@pytest.fixture
def create_basic_report_one_column_dict() -> Dict:
    """ Creates a report with basic info """
    return {TARGET_CN: ["test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target2",
                        "test_target3"]}


@pytest.fixture
def create_basic_report_dict_one_column_without_target() -> Dict:
    """ Creates a report dict with one column and several rows """
    return {SOCKET_CN: ["test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target",
                        "test_target2",
                        "test_target3"]}


@pytest.fixture
def create_report_several_columns_dict(create_basic_report_one_column_dict) -> Dict:
    """ Creates a report dict with several columns and rows """

    create_basic_report_one_column_dict[GROUPS_CN] = ["core", "core", "core",
                                                      "core", "core", "core",
                                                      "core", "core", "core",
                                                      "core", "core", "core",
                                                      "core2", "core3"]

    create_basic_report_one_column_dict[SOCKET_CN] = [0, 0, 0,
                                                      0, 0, 0,
                                                      0, 0, 0,
                                                      0, 0, 0,
                                                      0, 0]

    create_basic_report_one_column_dict[CORE_CN] = [0, 1, 2,
                                                    3, 4, 5,
                                                    6, 7, 8,
                                                    9, 10, 11,
                                                    0, 0]

    create_basic_report_one_column_dict[EVENT_CN] = ["CPU_CLK_THREAD_UNH", "CPU_CLK_THREAD_UNH_", "time_enabled",
                                                     "time_running", "LLC_MISES", "INSTRUCTIONS",
                                                     "CPU_CLK_THREAD_UNH", "CPU_CLK_THREAD_UNH_", "time_enabled",
                                                     "time_running", "LLC_MISES", "INSTRUCTIONS",
                                                     "test1", "test2"]

    create_basic_report_one_column_dict[EVENT_VALUE_CN] = [2849918, 49678, 4273969,
                                                           4273969, 71307, 2673428,
                                                           2849919, 49679, 4273970,
                                                           4273970, 71308, 2673429,
                                                           -1, -2]

    return create_basic_report_one_column_dict


@pytest.fixture
def create_hwpc_report_dict() -> Dict:
    """ Creates a hwpc report dict """
    return {
        TIMESTAMP_CN: "2022-03-31T10:03:13.686Z",
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
def create_hwpc_report_with_empty_cells_dict() -> Dict:
    """ Creates a hwpc report dict with empty cells"""

    return {TIMESTAMP_CN: "2022-03-31T10:03:13.686Z",
            SENSOR_CN: "test_sensor",
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
def compute_hwpc_msr_events_average(create_hwpc_report_with_empty_cells_dict):
    """ Compute the average of different msr events.

        Return:
            A dictionary with the averages
    """
    msr_group_dict = create_hwpc_report_with_empty_cells_dict[GROUPS_CN][MSR_GROUP]
    msr_event_average_dict = {}
    msr_event_number_dict = {}

    for _, socket_dict in msr_group_dict.items():
        for _, core_dict in socket_dict.items():
            for event_id, event_value in core_dict.items():
                if event_id not in msr_event_average_dict.keys():
                    msr_event_average_dict[event_id] = 0
                    msr_event_number_dict[event_id] = 0
                msr_event_average_dict[event_id] += event_value
                msr_event_number_dict[event_id] += 1

    for event_id in msr_event_average_dict.keys():
        msr_event_average_dict[event_id] /= msr_event_number_dict[event_id]

    return msr_event_average_dict

@pytest.fixture
def compute_hwpc_msr_events_sum(create_hwpc_report_with_empty_cells_dict):
    """ Compute the sum of different msr events.

        Return:
            A dictionary with the sum
    """
    msr_group_dict = create_hwpc_report_with_empty_cells_dict[GROUPS_CN][MSR_GROUP]
    msr_event_sum_dict = {}

    for _, socket_dict in msr_group_dict.items():
        for _, core_dict in socket_dict.items():
            for event_id, event_value in core_dict.items():
                if event_id not in msr_event_sum_dict.keys():
                    msr_event_sum_dict[event_id] = 0
                msr_event_sum_dict[event_id] += event_value

    return msr_event_sum_dict

@pytest.fixture
def compute_hwpc_core_events_sum(create_hwpc_report_dict):
    """ Compute the sum of different core events.

        Return:
            A dictionary with the sum
    """
    core_group_dict = create_hwpc_report_dict[GROUPS_CN][CORE_GROUP]
    core_event_sum_dict = {}

    for _, socket_dict in core_group_dict.items():
        for _, core_dict in socket_dict.items():
            for event_id, event_value in core_dict.items():
                if event_id not in core_event_sum_dict.keys():
                    core_event_sum_dict[event_id] = 0
                core_event_sum_dict[event_id] += event_value

    return core_event_sum_dict


@pytest.fixture
def get_hwpc_msr_events_from_dict(create_hwpc_report_with_empty_cells_dict):
    msr_events = []
    msr_group_dict = create_hwpc_report_with_empty_cells_dict[GROUPS_CN][MSR_GROUP]

    for _, socket_dict in msr_group_dict.items():
        for _, core_dict in socket_dict.items():
            for event_id in core_dict.keys():
                if event_id not  in msr_events:
                    msr_events.append(event_id)

    return msr_events

@pytest.fixture
def create_hwpc_report_dict_with_metadata(create_hwpc_report_dict) -> Dict:
    create_hwpc_report_dict[METADATA_CN] = {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                                            "predict": 0,
                                            "power_units": "watt"}
    return create_hwpc_report_dict


@pytest.fixture
def create_wrong_hwpc_report_dict() -> Dict:
    """ Creates a hwpc report dict with missing information """
    return {
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
def create_power_report_dict() -> Dict:
    """ Creates a report with basic info """
    return {
        TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT) + '+00:00',  # We are 00 hours and 00 minutes ahead of UTC
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target",
        POWER_CN: 5.5 * quantity.W}


@pytest.fixture
def create_power_report_dict_with_metadata() -> Dict:
    """ Creates a report with metadata and basic information """

    return {TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT) + '+00:00',
            # We are 00 hours and 00 minutes ahead of UTC
            SENSOR_CN: "test_sensor",
            TARGET_CN: "test_target2",
            POWER_CN: 10.5 * quantity.W,
            METADATA_CN: {"scope": "cpu", "socket": "0", "formula": "RAPL_ENERGY_PKG", "ratio": 1,
                          "predict": 0}}


@pytest.fixture
def create_power_report_influxdb_dict_with_metadata(create_report_dict_with_metadata) -> Dict:
    """ Creates the expected influx dict for a power report with metadata """

    metadata = create_report_dict_with_metadata[METADATA_CN]
    metadata[SENSOR_CN] = create_report_dict_with_metadata[SENSOR_CN]
    metadata[TARGET_CN] = create_report_dict_with_metadata[TARGET_CN]
    metadata[UNIT_CN] = str(create_report_dict_with_metadata[POWER_CN].units)

    return {TIME_CN: create_report_dict_with_metadata[TIMESTAMP_CN],
            TAGS_CN: metadata,
            FIELDS_CN: {POWER_CN: create_report_dict_with_metadata[POWER_CN].magnitude},
            MEASUREMENT_CN: MEASUREMENT_NAME}


@pytest.fixture
def create_influxdb_power_dict(create_power_report_dict) -> Dict:
    """ Creates the expected influx dict for a power report without metadata """
    # TIME_CN: time.mktime(datetime.strptime(create_report_dict[TIMESTAMP_CN],
    #                                                    DATE_FORMAT).timetuple())
    return {TIME_CN: create_power_report_dict[TIMESTAMP_CN],
            TAGS_CN: {UNIT_CN: str(create_power_report_dict[POWER_CN].units),
                      SENSOR_CN: create_power_report_dict[SENSOR_CN],
                      TARGET_CN: create_power_report_dict[TARGET_CN]},
            FIELDS_CN: {POWER_CN: create_power_report_dict[POWER_CN].magnitude},
            MEASUREMENT_CN: MEASUREMENT_NAME}


@pytest.fixture
def create_influxdb_power_dict_with_metadata(create_power_report_dict_with_metadata) -> Dict:
    """ Creates the expected influx dict for a power report without metadata """
    tags = create_power_report_dict_with_metadata[METADATA_CN]
    tags[UNIT_CN] = str(create_power_report_dict_with_metadata[POWER_CN].units)
    tags[SENSOR_CN] = create_power_report_dict_with_metadata[TARGET_CN]
    return {TIME_CN: create_power_report_dict_with_metadata[TIMESTAMP_CN],
            TAGS_CN: tags,
            FIELDS_CN: {POWER_CN: create_power_report_dict_with_metadata[POWER_CN].magnitude},
            MEASUREMENT_CN: MEASUREMENT_NAME}


@pytest.fixture
def create_wrong_power_report_dict() -> Dict:
    """ Creates a report with missing power info """
    return {
        TIMESTAMP_CN: datetime.now().strftime(DATE_FORMAT) + '+00:00',  # We are 00 hours and 00 minutes ahead of UTC
        SENSOR_CN: "test_sensor",
        TARGET_CN: "test_target"}
