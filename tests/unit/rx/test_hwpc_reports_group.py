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
from powerapi.exception import BadInputDataException
from powerapi.rx.hwpc_reports_group import HWPCReportsGroup, SOCKET_CN, CORE_CN, EVENT_CN, EVENT_VALUE_CN, GROUPS_CN
from powerapi.rx.reports_group import TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN
from tests.unit.rx.util import create_hwpc_report_dict, create_hwpc_report_with_empty_cells_dict, \
    create_hwpc_report_dict_with_metadata, create_wrong_hwpc_report_dict


##############################
#
# Tests
#
##############################
def test_of_create_hwpc_reports_group_from_one_dict(create_hwpc_report_dict):
    """Test if a HWPC report group is well-built"""

    # Setup
    reports_dict = [create_hwpc_report_dict]

    # Exercise
    reports_group_to_check = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == {}  # There is no metadata
    assert reports_group_to_check.sensor == create_hwpc_report_dict[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_hwpc_report_dict[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 1
    assert create_hwpc_report_dict[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 6
    assert TARGET_CN in reports_group_to_check.report.columns
    assert SOCKET_CN in reports_group_to_check.report.columns
    assert CORE_CN in reports_group_to_check.report.columns
    assert EVENT_CN in reports_group_to_check.report.columns
    assert EVENT_VALUE_CN in reports_group_to_check.report.columns
    assert GROUPS_CN in reports_group_to_check.report.columns


def test_of_create_hwpc_reports_group_from_two_dicts(create_hwpc_report_dict, create_hwpc_report_with_empty_cells_dict):
    """Test if a HWPC report group is well-built with multiples reports """
    # Setup
    reports_dict = [create_hwpc_report_dict, create_hwpc_report_with_empty_cells_dict]

    # Exercise
    reports_group_to_check = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == {}  # There is no metadata
    assert reports_group_to_check.sensor == create_hwpc_report_dict[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_hwpc_report_with_empty_cells_dict[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 2
    assert create_hwpc_report_dict[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert create_hwpc_report_with_empty_cells_dict[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 6
    assert TARGET_CN in reports_group_to_check.report.columns
    assert SOCKET_CN in reports_group_to_check.report.columns
    assert CORE_CN in reports_group_to_check.report.columns
    assert EVENT_CN in reports_group_to_check.report.columns
    assert EVENT_VALUE_CN in reports_group_to_check.report.columns
    assert GROUPS_CN in reports_group_to_check.report.columns


def test_of_create_hwpc_reports_group_from_one_dict_with_metadata(create_hwpc_report_dict_with_metadata):
    """Test if a HWPC report group is well-built with one report with metadata """
    # Setup
    reports_dict = [create_hwpc_report_dict_with_metadata]

    # Exercise
    reports_group_to_check = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Check that reports group is well-built
    assert reports_group_to_check is not None
    assert reports_group_to_check.metadata == create_hwpc_report_dict_with_metadata[METADATA_CN]  # There is no metadata
    assert reports_group_to_check.sensor == create_hwpc_report_dict_with_metadata[SENSOR_CN]
    assert reports_group_to_check.timestamp == create_hwpc_report_dict_with_metadata[TIMESTAMP_CN]
    assert len(reports_group_to_check.report.get_targets()) == 1
    assert create_hwpc_report_dict_with_metadata[TARGET_CN] in reports_group_to_check.report.get_targets()
    assert len(reports_group_to_check.report.columns) == 6
    assert TARGET_CN in reports_group_to_check.report.columns
    assert SOCKET_CN in reports_group_to_check.report.columns
    assert CORE_CN in reports_group_to_check.report.columns
    assert EVENT_CN in reports_group_to_check.report.columns
    assert EVENT_VALUE_CN in reports_group_to_check.report.columns
    assert GROUPS_CN in reports_group_to_check.report.columns


def test_of_create_hwpc_reports_group_from_wrong_dict_fails(create_wrong_hwpc_report_dict):
    """ Test if the creation of a HWPC report group fails with a wrong dictionary """

    # Setup
    reports_dict = [create_wrong_hwpc_report_dict]

    # Exercise
    reports_group_to_check = None
    try:
        reports_group_to_check = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)
        assert False, "create_reports_group_from_dicts should fails!"
    except BadInputDataException:
        pass

    assert reports_group_to_check is None


def test_of_to_mongodb_hwpc_with_one_report(create_hwpc_report_dict):
    """ Test if tp_mongodb creates the dict correctly """
    # Setup
    reports_dict = [create_hwpc_report_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    reports_dict_to_check = reports_group.to_mongodb_dict()

    # Check
    assert len(reports_dict_to_check) == 1
    assert reports_dict_to_check[0] == create_hwpc_report_dict


def test_of_to_mongodb_hwpc_with_two_reports(create_hwpc_report_dict, create_hwpc_report_with_empty_cells_dict):
    """ Test if tp_mongodb creates the dict correctly """
    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    reports_dict_to_check = reports_group.to_mongodb_dict()

    # Check
    assert len(reports_dict_to_check) == 2

    for current_report_dict in reports_dict_to_check:
        if current_report_dict[TARGET_CN] == 'all':
            assert current_report_dict == create_hwpc_report_with_empty_cells_dict
        else:
            assert current_report_dict == create_hwpc_report_dict
