# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from copy import deepcopy

import pytest
from powerapi.report import *
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel


"""
Test HWPCDispatcheRule

When testing on HWPC report, we test to get formula id for this reports

report_1 : one group, one socket, one CPU
report_2 : one group, two socket, one CPU per socket
report_3 : one group, two socket, two CPU per socket

each report could be associated with a RAPL group that contain one socket and
one CPU

"""

CPU_1 = create_core_report('1', 'e0', '0')
CPU_2 = create_core_report('2', 'e0', '1')
CPU_3 = create_core_report('3', 'e0', '2')
CPU_4 = create_core_report('4', 'e0', '3')

SOCKET_1 = create_socket_report('1', [CPU_1])
SOCKET_2 = create_socket_report('1', [CPU_1, CPU_2])
SOCKET_3 = create_socket_report('2', [CPU_3, CPU_4])

GROUP_1 = create_group_report('1', [SOCKET_1])
GROUP_2 = create_group_report('1', [SOCKET_2])
GROUP_3 = create_group_report('1', [SOCKET_2, SOCKET_3])
RAPL = create_group_report('RAPL', [SOCKET_1])

REPORT_1 = create_report_root([GROUP_1])
REPORT_2 = create_report_root([GROUP_2])
REPORT_3 = create_report_root([GROUP_3])

REPORT_1_RAPL = create_report_root([GROUP_1, RAPL])
REPORT_2_RAPL = create_report_root([GROUP_2, RAPL])
REPORT_3_RAPL = create_report_root([GROUP_3, RAPL])

BAD_REPORT_1 = create_report_root([])
BAD_REPORT_2 = create_report_root([create_group_report('1', [])])
BAD_REPORT_3 = create_report_root([create_group_report('1', [
    create_socket_report('1', [])])])
BAD_REPORT_4 = create_report_root([create_group_report('1', [
    create_socket_report('1', [HWPCReportCore('1')])])])


############
# Fixtures #
############
@pytest.fixture(params=[BAD_REPORT_1, BAD_REPORT_2, BAD_REPORT_3, BAD_REPORT_4])
def bad_report(request):
    return request.param


@pytest.fixture(params=[REPORT_1, REPORT_2, REPORT_3, REPORT_1_RAPL,
                        REPORT_2_RAPL, REPORT_3_RAPL])
def report(request):
    return request.param


@pytest.fixture(params=[REPORT_1, REPORT_1_RAPL])
def report_1(request):
    return request.param


@pytest.fixture(params=[REPORT_2, REPORT_2_RAPL])
def report_2(request):
    return request.param


@pytest.fixture(params=[REPORT_3, REPORT_3_RAPL])
def report_3(request):
    return request.param


#########
# UTILS #
#########
def validate_formula_id(formula_id_list, validation_list):
    """
    assert if every element in formula_id_list are in validation list and
    vice versa

    validation_list must be sorted
    """
    assert len(formula_id_list) == len(validation_list)
    formula_id_list.sort()
    
    for a, b in zip(formula_id_list, validation_list):
        assert a == b


#########################
# TEST REPORT STRUCTURE #
#########################

def test_init_fields_name_test():
    """
    test if the field's names of the dispatch_rule identifier tuple are
    correctly initialized
    """
    assert HWPCDispatchRule(HWPCDepthLevel.TARGET).fields == ['target']
    assert HWPCDispatchRule(HWPCDepthLevel.ROOT).fields == ['sensor']
    assert HWPCDispatchRule(HWPCDepthLevel.SOCKET).fields == ['sensor',
                                                              'socket']
    assert HWPCDispatchRule(HWPCDepthLevel.CORE).fields == ['sensor', 'socket',
                                                            'core']


######################
# TEST ON BAD REPORT #
######################
def test_get_formula_id_from_bad_report(bad_report):
    """
    get formula id from  bad formated reports to four dispatcher rule :
    - dispatch by sensor
    - dispatch by target
    - dispatch by socket
    - dispatch by cpu

    bad formated reports are reports without events, cpus dictionary, sockets 
    dictionary or groups dictionary

    the method must return an empty list
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.ROOT).get_formula_id(bad_report)
    validate_formula_id(ids, [])

    ids = HWPCDispatchRule(HWPCDepthLevel.TARGET).get_formula_id(bad_report)
    validate_formula_id(ids, [])

    ids = HWPCDispatchRule(HWPCDepthLevel.SOCKET).get_formula_id(bad_report)
    validate_formula_id(ids, [])

    ids = HWPCDispatchRule(HWPCDepthLevel.CORE).get_formula_id(bad_report)
    validate_formula_id(ids, [])


####################################
# TEST DISPATCH BY ROOT AND TARGET #
####################################
def test_get_formula_id_sensor_rule(report):
    """
    get formula id from reports with a rule that dispatch by sensor :

    the method must return this list :
    [('toto',)]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.ROOT).get_formula_id(report)
    validate_formula_id(ids, [('toto',)])


def test_get_formula_id_target_rule(report):
    """
    get formula id from reports with a rule that dispatch by target :

    the method must return this list :
    [('system',)]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.TARGET).get_formula_id(report)
    validate_formula_id(ids, [('system',)])


###########################
# TEST DISPATCH BY SOCKET #
###########################
def test_get_formula_id_socket_rule_report_1(report_1):
    """
    get formula id from report1 with a rule that dispatch by socket :

    the method must return this list :
    [('toto','1')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.SOCKET).get_formula_id(report_1)
    validate_formula_id(ids, [('toto', '1')])


def test_get_formula_id_socket_rule_report_2(report_2):
    """
    get formula id from report2 with a rule that dispatch by socket :

    the method must return this list :
    [('toto','1'), ('toto','2')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.SOCKET).get_formula_id(report_2)
    validate_formula_id(ids,  [('toto', '1')])


def test_get_formula_id_socket_rule_report_3(report_3):
    """
    get formula id from report3 with a rule that dispatch by socket :

    the method must return this list :
    [('toto','1'), ('toto','2')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.SOCKET).get_formula_id(report_3)
    validate_formula_id(ids, [('toto', '1'), ('toto', '2')])


#########################
# TEST DISPATCH BY CORE #
#########################
def test_get_formula_id_cpu_rule_report_1(report_1):
    """
    get formula id from report1 with a rule that dispatch by cpu :

    the method must return this list :
    [('toto','1', '1')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.CORE).get_formula_id(report_1)
    validate_formula_id(ids, [('toto', '1', '1')])


def test_get_formula_id_cpu_rule_report_2(report_2):
    """
    get formula id from report2 with a rule that dispatch by cpu :

    the method must return this list :
    [('toto','1', '1'), ('toto','2', '2')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.CORE).get_formula_id(report_2)
    validate_formula_id(ids, [('toto', '1', '1'), ('toto', '1', '2')])


def test_get_formula_id_cpu_rule_report_3(report_3):
    """
    get formula id from report3 with a rule that dispatch by cpu :

    the method must return this list :
    [('toto','1', '1'), ('toto','1', '2'), ('toto','2', '3'), ('toto','2', '3')]
    """
    ids = HWPCDispatchRule(HWPCDepthLevel.CORE).get_formula_id(report_3)
    validate_formula_id(ids, [('toto', '1', '1'), ('toto', '1', '2'),
                              ('toto', '2', '3'), ('toto', '2', '4')])
