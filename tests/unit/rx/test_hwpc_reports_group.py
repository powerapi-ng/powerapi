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
from powerapi.rx.hwpc_reports_group import HWPCReportsGroup, SOCKET_CN, CORE_CN, EVENT_CN, EVENT_VALUE_CN, GROUPS_CN, \
    MSR_GROUP, CORE_GROUP
from powerapi.rx.reports_group import TIMESTAMP_CN, SENSOR_CN, TARGET_CN, METADATA_CN
from tests.unit.rx.util import create_hwpc_report_dict, create_hwpc_report_with_empty_cells_dict, \
    create_hwpc_report_dict_with_metadata, create_wrong_hwpc_report_dict, compute_hwpc_msr_events_average, \
    get_hwpc_msr_events_from_dict, compute_hwpc_msr_events_sum, compute_hwpc_core_events_sum


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


def test_of_compute_event_average(create_hwpc_report_with_empty_cells_dict, compute_hwpc_msr_events_average):
    """ Test if an event average is computed correctly """
    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    mperf_average_to_check = reports_group.compute_event_average(event_name="mperf", group="msr", target="all",
                                                                 socket="0")
    aperf_average_to_check = reports_group.compute_event_average(event_name="aperf", group="msr", target="all",
                                                                 socket="0")
    tsc_average_to_check = reports_group.compute_event_average(event_name="TSC", group="msr", target="all",
                                                               socket="0")

    time_enabled_average_to_check = reports_group.compute_event_average(event_name="time_enabled", group="msr",
                                                                        target="all",
                                                                        socket="0")

    time_running_average_to_check = reports_group.compute_event_average(event_name="time_running", group="msr",
                                                                        target="all",
                                                                        socket="0")

    invalid_event_average_to_check = reports_group.compute_event_average(event_name="no_event", group="msr",
                                                                         target="all",
                                                                         socket="0")

    # Check
    assert mperf_average_to_check == compute_hwpc_msr_events_average["mperf"]
    assert aperf_average_to_check == compute_hwpc_msr_events_average["aperf"]
    assert tsc_average_to_check == compute_hwpc_msr_events_average["TSC"]
    assert time_enabled_average_to_check == compute_hwpc_msr_events_average["time_enabled"]
    assert time_running_average_to_check == compute_hwpc_msr_events_average["time_running"]
    assert invalid_event_average_to_check is None


def test_of_get_group_events(create_hwpc_report_with_empty_cells_dict, get_hwpc_msr_events_from_dict):
    """ Check of all msr events are returned """
    """ Test if an event average is computed correctly """
    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    msr_events_to_check = reports_group.get_group_events(MSR_GROUP)
    empty_events_to_check = reports_group.get_group_events("xx")

    # Check
    assert len(msr_events_to_check) == len(get_hwpc_msr_events_from_dict)
    assert len(empty_events_to_check) == 0

    for event in msr_events_to_check:
        assert event in get_hwpc_msr_events_from_dict


def test_of_compute_group_event_averages(create_hwpc_report_with_empty_cells_dict, compute_hwpc_msr_events_average):
    """ Check that all msr event averages are well computed """

    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    averages_to_check = reports_group.compute_group_event_averages(group=MSR_GROUP, target="all", socket="0")
    invalid_averages_to_check = reports_group.compute_group_event_averages(group=MSR_GROUP, target="al1l", socket="0")
    invalid_averages_to_check_2 = reports_group.compute_group_event_averages(group="XX", target="all", socket="0")

    # Check
    assert averages_to_check == compute_hwpc_msr_events_average
    assert invalid_averages_to_check is None
    assert invalid_averages_to_check_2 is None


def test_of_compute_group_event_sum(create_hwpc_report_with_empty_cells_dict, compute_hwpc_msr_events_sum):
    """ Check that all msr event sum are well computed """

    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    sum_to_check = reports_group.compute_group_event_sum(group=MSR_GROUP, target="all", socket="0")
    invalid_sum_to_check = reports_group.compute_group_event_sum(group=MSR_GROUP, target="al1l", socket="0")
    invalid_sum_to_check_2 = reports_group.compute_group_event_sum(group="XX", target="all", socket="0")

    # Check
    assert sum_to_check == compute_hwpc_msr_events_sum
    assert invalid_sum_to_check is None
    assert invalid_sum_to_check_2 is None


def test_of_compute_group_event_sum_excluding_target(create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict,
                                                     compute_hwpc_core_events_sum):
    """ Check that all core event sum are well computed """

    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    sum_to_check = reports_group.compute_group_event_sum_excluding_target(group=CORE_GROUP, target="all",
                                                                          socket="socket1")
    invalid_sum_to_check = reports_group.compute_group_event_sum_excluding_target(group=CORE_GROUP, target="al1l",
                                                                                  socket="0")
    invalid_sum_to_check_2 = reports_group.compute_group_event_sum_excluding_target(group="XX", target="all",
                                                                                    socket="0")

    # Check
    assert sum_to_check == compute_hwpc_core_events_sum
    assert invalid_sum_to_check is None
    assert invalid_sum_to_check_2 is None


def test_of_get_event_value(create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict):
    """ Check that an event value is retriebed """

    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    event_val_to_check = reports_group.get_event_value(target="all", group="msr", socket="0", core="3",
                                                       event_name="aperf")

    wrong_event_val_to_check = reports_group.get_event_value(target="all", group="msr", socket="0", core="3",
                                                             event_name="aperf99")

    # Check
    assert event_val_to_check == 24521456
    assert wrong_event_val_to_check is None


def test_of_get_event_value_first_found_core(create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict):
    """ Check that an event value is retrieved """

    # Setup
    reports_dict = [create_hwpc_report_with_empty_cells_dict, create_hwpc_report_dict]
    reports_group = HWPCReportsGroup.create_reports_group_from_dicts(reports_dict)

    # Exercise
    event_val_to_check = reports_group.get_event_value_first_found_core(target="all", group="msr", socket="0",
                                                       event_name="aperf")

    wrong_event_val_to_check = reports_group.get_event_value_first_found_core(target="all", group="msr", socket="0",
                                                             event_name="aperf99")

    # Check
    assert event_val_to_check == 14511032
    assert wrong_event_val_to_check is None
