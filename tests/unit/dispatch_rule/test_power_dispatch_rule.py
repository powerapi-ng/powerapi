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
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.#
import pytest

from powerapi.report import PowerReport
from powerapi.dispatch_rule import PowerDispatchRule, PowerDepthLevel

TS1 = 0
SENSOR1= 'sensor1'
TARGET1 = 'target1'

@pytest.fixture
def report1_socket0():
    return PowerReport(TS1, SENSOR1, TARGET1, 1234, {'socket': 0, 'core': 0})


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

def test_get_formula_id_with_sensor_rule_must_return_good_id(report1_socket0):
    """
    get formula id from reports with a rule that dispatch by sensor :
    """
    ids = PowerDispatchRule(PowerDepthLevel.SENSOR).get_formula_id(report1_socket0)
    validate_formula_id(ids, [(SENSOR1,)])


def test_get_formula_id_with_target_rule_must_return_good_id(report1_socket0):
    """
    get formula id from reports with a rule that dispatch by target :
    """
    ids = PowerDispatchRule(PowerDepthLevel.TARGET).get_formula_id(report1_socket0)
    validate_formula_id(ids, [(TARGET1,)])

def test_get_formula_id_with_socket_rule_must_return_good_id(report1_socket0):
    """
    get formula id from reports with a rule that dispatch by target :
    """
    ids = PowerDispatchRule(PowerDepthLevel.SOCKET).get_formula_id(report1_socket0)
    validate_formula_id(ids, [(SENSOR1, 0)])

def test_get_formula_id_with_core_rule_must_return_good_id(report1_socket0):
    """
    get formula id from reports with a rule that dispatch by target :
    """
    ids = PowerDispatchRule(PowerDepthLevel.CORE).get_formula_id(report1_socket0)
    validate_formula_id(ids, [(SENSOR1, 0, 0)])
