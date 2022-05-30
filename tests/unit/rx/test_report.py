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
import pytest

from typing import Dict, Any

from tests.unit.rx.util import create_basic_report_one_column_dict, create_report_several_columns_dict, \
    create_basic_report_dict_one_column_without_target

from powerapi.rx.hwpc_reports_group import GROUPS_CN, SOCKET_CN, CORE_CN, EVENT_CN, EVENT_VALUE_CN
from powerapi.rx.report import Report, TARGET_CN


##############################
#
# Constants
#
##############################


##############################
#
# Fixtures
#
##############################


@pytest.fixture
def create_report_dict_with_several_columns(create_basic_report_one_column_dict) -> Dict:
    """ Creates a report dict with data """

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
def create_basic_report_from_dict(create_basic_report_one_column_dict) -> Report:
    """ Creates a fake report by using the given information

        Args:
            report_dict: Dictionary that contains information of the report
    """

    return Report(data=create_basic_report_one_column_dict)


@pytest.fixture
def create_basic_report_from_dict_without_target(create_basic_report_dict_one_column_without_target) -> Report:
    """ Creates a fake report by using the given information

        Args:
            report_dict: Dictionary that contains information of the report
    """

    return Report(data=create_basic_report_dict_one_column_without_target)


@pytest.fixture
def create_basic_report_several_cols_from_dict(create_report_dict_with_several_columns: Dict[str, Any]) -> Report:
    """ Creates a fake report by using the given information

        Args:
            report_dict: Dictionary that contains information of the report
    """

    return Report(data=create_report_dict_with_several_columns)


##############################
#
# Tests
#
##############################


def test_of_get_targets_from_one_column_report(create_basic_report_from_dict, create_basic_report_one_column_dict):
    """Test if a basic report is well-built"""

    # Setup
    report_dict = create_basic_report_one_column_dict
    report = create_basic_report_from_dict

    # Exercise
    targets = report.get_targets()

    # Check that targets are presented report is well-built
    for current_target in report_dict[TARGET_CN]:
        assert current_target in targets

    assert len(targets) == 3  # Only three targets exist


def test_of_get_targets_from_several_column_report(create_basic_report_several_cols_from_dict,
                                                   create_report_dict_with_several_columns):
    """ Test that a report with several rows/columns is well-built"""

    # Setup
    report_dict = create_report_dict_with_several_columns
    report = create_basic_report_several_cols_from_dict

    # Exercise
    targets = report.get_targets()

    # Check that targets are presented report is well-built
    for current_target in report_dict[TARGET_CN]:
        assert current_target in targets

    assert len(targets) == 3  # Only three targets exist


def test_of_get_targets_fails_if_target_is_no_present(create_basic_report_from_dict_without_target):
    """ Test of get target fails"""

    # Setup
    report = create_basic_report_from_dict_without_target

    # Exercise
    targets = None
    try:
        targets = report.get_targets()
        assert False, "get_targets should fails!"
    except KeyError:
        pass
    # Check that targets is empty
    assert targets is None
