# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.#
from datetime import datetime
from copy import deepcopy
import pytest
from powerapi.report import HWPCReport
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

def create_core_report(core_id, event_id, event_value, events=None):
    id_str = str(core_id)
    data = {id_str: {}}
    if events is not None:
        data[id_str] = events
        return data
    data[id_str] = {event_id: event_value}
    return data


def create_socket_report(socket_id, core_list):
    id_str = str(socket_id)
    data = {id_str: {}}
    for core in core_list:
        data[id_str].update(core)
    return data


def create_group_report(group_id, socket_list):
    group = {}
    for socket in socket_list:
        group.update(socket)
    return (group_id, group)


def create_report_root(group_list, timestamp=datetime.fromtimestamp(0), sensor='toto', target='system'):
    sensor = HWPCReport(timestamp=timestamp, sensor=sensor, target=target, groups={})
    for (group_id, group) in group_list:
        sensor.groups[group_id] = group
    return sensor

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


############
# Fixtures #
############
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
    [('toto','1', '1'), ('toto','1', '2')]
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
