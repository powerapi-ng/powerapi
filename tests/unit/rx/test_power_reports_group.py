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
# Last modified : 19 Mai 2022

##############################
#
# Imports
#
##############################
import time
from datetime import datetime
from typing import Dict

from powerapi.exception import BadInputDataException
from powerapi.rx.power_reports_group import PowerReportsGroup, POWER_CN
from powerapi.rx.report import TARGET_CN
from powerapi.rx.reports_group import SENSOR_CN, TIMESTAMP_CN, METADATA_CN, TAGS_CN, TIME_CN

from tests.unit.rx.util import create_power_report_dict, create_power_report_dict_with_metadata, \
    create_wrong_power_report_dict, create_influxdb_power_dict, create_influxdb_power_dict_with_metadata

##############################
#
# Tests
#
##############################


def test_of_create_power_reports_group_from_dict(create_power_report_dict):
    """Test if a basic report is well-built"""

    # Setup
    reports_dict = [create_power_report_dict]

    # Exercise
    reports_group_to_check = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == {}  # There is no metadata
    assert reports_group_to_check.sensor == create_power_report_dict[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_power_report_dict[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 1
    assert create_power_report_dict[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 2
    assert TARGET_CN in reports_group_to_check.report.columns
    assert POWER_CN in reports_group_to_check.report.columns


def test_of_create_power_reports_group_from_two_dicts(create_power_report_dict, create_power_report_dict_with_metadata):
    """ Test if a HWPC report group is well-built with multiples reports """
    # Setup
    reports_dict = [create_power_report_dict, create_power_report_dict_with_metadata]

    # Exercise
    reports_group_to_check = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == {}  # There is no metadata
    assert reports_group_to_check.sensor == create_power_report_dict_with_metadata[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_power_report_dict[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 2
    assert create_power_report_dict[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert create_power_report_dict_with_metadata[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 2
    assert TARGET_CN in reports_group_to_check.report.columns
    assert POWER_CN in reports_group_to_check.report.columns


def test_of_create_power_reports_group_from_one_dict_with_metadata(create_power_report_dict_with_metadata):
    """Test if a Power report group is well-built with one report with metadata """
    # Setup
    reports_dict = [create_power_report_dict_with_metadata]

    # Exercise
    reports_group_to_check = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == create_power_report_dict_with_metadata[METADATA_CN]  # There is metadata
    assert reports_group_to_check.sensor == create_power_report_dict_with_metadata[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_power_report_dict_with_metadata[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 1
    assert create_power_report_dict_with_metadata[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 2
    assert TARGET_CN in reports_group_to_check.report.columns
    assert POWER_CN in reports_group_to_check.report.columns


def test_of_create_power_reports_group_from_wrong_dict_fails(create_wrong_power_report_dict):
    """ Test if the creation of a HWPC report group fails with a wrong dictionary """

    # Setup
    reports_dict = [create_wrong_power_report_dict]

    # Exercise
    reports_group_to_check = None
    try:
        reports_group_to_check = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)
        assert False, "create_reports_group_from_dicts should fails!"
    except BadInputDataException:
        pass

    assert reports_group_to_check is None


def test_of_to_mongodb_power_with_one_report(create_power_report_dict):
    """ Test if tp_mongodb creates the dict correctly """
    # Setup
    reports_dict = [create_power_report_dict]
    reports_group = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    reports_dict_to_check = reports_group.to_mongodb_dict()

    # Check
    assert len(reports_dict_to_check) == 1
    assert reports_dict_to_check[0] == create_power_report_dict


def test_of_to_mongodb_power_with_two_reports(create_power_report_dict, create_power_report_dict_with_metadata):
    """ Test if to_mongodb_dict creates the dict correctly """
    # Setup
    create_power_report_dict[TIMESTAMP_CN] = create_power_report_dict_with_metadata[TIMESTAMP_CN]
    create_power_report_dict[METADATA_CN] = create_power_report_dict_with_metadata[METADATA_CN]
    reports_dict = [create_power_report_dict_with_metadata, create_power_report_dict]
    reports_group = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    reports_dict_to_check = reports_group.to_mongodb_dict()

    # Check
    assert len(reports_dict_to_check) == 2

    for current_report_dict in reports_dict_to_check:
        if current_report_dict[TARGET_CN] == 'test_target2':
            assert current_report_dict == create_power_report_dict_with_metadata
        else:
            assert current_report_dict == create_power_report_dict


def test_of_to_influx_power_with_one_report(create_power_report_dict, create_influxdb_power_dict):
    """ Test if to_influx_dict creates the dict correctly """
    # Setup
    reports_dict = [create_power_report_dict]
    reports_group = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    reports_dict_to_check = reports_group.to_influx_dict()

    # Check
    assert len(reports_dict_to_check) == 1
    assert reports_dict_to_check[0] == create_influxdb_power_dict


def test_of_to_influx_power_with_two_reports(create_power_report_dict, create_power_report_dict_with_metadata,
                                             create_influxdb_power_dict, create_influxdb_dict_with_metadata):
    """ Test if to_influx_dict creates the dict correctly """
    # Setup
    reports_dict = [create_power_report_dict_with_metadata,create_power_report_dict]
    reports_group = PowerReportsGroup.create_reports_group_from_dicts(reports_dict)
    create_influxdb_power_dict[TAGS_CN] = create_influxdb_dict_with_metadata[TAGS_CN]
    create_influxdb_power_dict[TIME_CN] = create_influxdb_dict_with_metadata[TIME_CN]

    # Exercise
    reports_dict_to_check = reports_group.to_influx_dict()

    # Check
    assert len(reports_dict_to_check) == 2

    for current_report_dict in reports_dict_to_check:
        if current_report_dict[TAGS_CN][TARGET_CN] == 'test_target2':
            assert current_report_dict == create_influxdb_dict_with_metadata
        else:
            assert current_report_dict == create_influxdb_power_dict
