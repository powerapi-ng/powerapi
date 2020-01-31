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
from powerapi.report.report import DeserializationFail
from powerapi.report.hwpc_report import HWPCReport

@pytest.mark.parametrize("json_input", [
    ({"timestamp": datetime.datetime.now(),
      "sensor": "fake-sensor",
      "target": "fake-target",
      "groups": {}})
]
)
def test_deserialize_good_hwpc_report_work(json_input):
    """
    Test working input for HWPCReport deserialize
    :param json_input: Data in input
    """
    HWPCReport.deserialize(json_input)
    assert True


@pytest.mark.parametrize("json_input", [
    ({"sensor": "fake-sensor",
      "target": "fake-target",
      "groups": {}}),
    ({"timestamp": datetime.datetime.now(),
      "target": "fake-target",
      "groups": {}}),
    ({"timestamp": datetime.datetime.now(),
      "sensor": "fake-sensor",
      "groups": {}}),
    ({"timestamp": datetime.datetime.now(),
      "sensor": "fake-sensor",
      "target": "fake-target"})
]
)
def test_deserialize_bad_hwpc_report_fail(json_input):
    with pytest.raises(DeserializationFail):
        HWPCReport.deserialize(json_input)
