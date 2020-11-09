# Copyright (c) 2018, INRIA Copyright (c) 2018, University of Lille All rights
# reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

import pytest

from powerapi.formula import FormulaActor


def test_create_a_FormulaActor_with_empty_name_must_add_no_value_in_FormulaState_metadata():
    actor = FormulaActor('(,)', [], )
    assert actor.state.metadata == {}


def test_create_a_FormulaActor_with_name_that_contains_only_sensor_name_must_add_sensor_name_in_FormulaState_metadata():
    actor = FormulaActor('(\'DISPATCHER_NAME\',\'SENSOR_NAME\',)', [], )
    assert actor.state.metadata == {'sensor': 'SENSOR_NAME'}


def test_create_a_FormulaActor_with_name_that_contains_sensor_name_and_socket_id_must_add_sensor_name_and_socket_id_in_FormulaState_metadata():
    actor = FormulaActor('(\'DISPATCHER_NAME\',\'SENSOR_NAME\',\'0\')', [], )
    assert actor.state.metadata == {'sensor': 'SENSOR_NAME', 'socket': 0}


def test_create_a_FormulaActor_with_name_that_contains_sensor_name_socket_id_and_core_id_must_add_sensor_name_socket_id_and_core_id_in_FormulaState_metadata():
    actor = FormulaActor('\'DISPATCHER_NAME\',(\'SENSOR_NAME\',\'0\',\'1\')', [], )
    assert actor.state.metadata == {'sensor': 'SENSOR_NAME', 'socket': 0, 'core': 1}


