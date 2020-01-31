"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pytest
import datetime
from powerapi.report_model.hwpc_model import HWPCModel, BadInputData

@pytest.fixture()
def hwpc_model():
    """
    :return: HWPCModel
    """
    return HWPCModel()

##############################################################################
#                                Tests                                       #
##############################################################################

####################
# MongoDB
####################


@pytest.mark.parametrize("json_input", [
    ({"_id": "fake-id",
      "timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor",
      "target": "fake-target",
      "groups": {}})
]
)
def test_convert_hwpc_report_from_mongodb_work(hwpc_model, json_input):
    """
    Test working input for HWPCReport from_mongodb
    :param json_input: Data in input
    """
    hwpc_model.from_mongodb(json_input)
    assert True


####################
# CsvDB
####################


@pytest.mark.parametrize("json_input", [
    ({"timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor",
      "target": "fake-target",
      "socket": 0,
      "cpu": 0,
      "event1": 1000,
      "event2": 2000}),
    ({"timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor",
      "target": "fake-target",
      "socket": 0,
      "cpu": 0}),
]
)
def test_convert_hwpc_report_from_csvdb_work(hwpc_model, json_input):
    """
    :param json_input: Data in input
    """
    hwpc_model.from_mongodb(json_input)
    assert True


@pytest.mark.parametrize("json_input", [
    ({"sensor": "fake-sensor",
      "target": "fake-target"}),
    ({"timestamp": datetime.datetime.now().timestamp(),
      "target": "fake-target"}),
    ({"timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor"}),
    ({"timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor",
      "target": "fake-target"}),
    ({"timestamp": datetime.datetime.now().timestamp(),
      "sensor": "fake-sensor",
      "target": "fake-target",
      "socket": 0}),
     ({"timestamp": datetime.datetime.now().timestamp(),
       "sensor": "fake-sensor",
       "target": "fake-target",
       "cpu": 0}),
]
)
def test_hwpc_report_from_csvdb_fail(hwpc_model, json_input):
    """
    :param json_input: Data in input
    """
    with pytest.raises(BadInputData):
        hwpc_model.from_csvdb("fake-name", json_input)
