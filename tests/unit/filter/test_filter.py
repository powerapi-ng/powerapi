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
from powerapi.filter import Filter, FilterUselessError
from powerapi.report import HWPCReport, create_report_root
from powerapi.report_model import HWPCModel
from powerapi.database import MongoDB

from tests.mongo_utils import gen_base_test_unit_filter, clean_base_test_unit_filter
from tests.mongo_utils import clean_base_test_unit_filter


URI = "mongodb://localhost:27017"


@pytest.fixture
def database():
    gen_base_test_unit_filter(URI)
    yield None
    clean_base_test_unit_filter(URI)


class TestFilter:

    def test_without_filter(self):
        """ Test filter without any filter, raise an error """
        hwpc_filter = Filter()
        with pytest.raises(FilterUselessError) as pytest_wrapped:
            hwpc_filter.route(create_report_root({}))
        assert pytest_wrapped.type == FilterUselessError


    def test_with_two_filter(self, database):
        """
        Test filter with two filter
        - 2 first report return first dispatcher
        - 2 next report return first and second dispatcher
        - 2 next report return None
        """
        mongodb = MongoDB(URI, "test_filter",
                          "test_filter1", report_model=HWPCModel())
        mongodb.connect()
        hwpc_filter = Filter()
        hwpc_filter.filter(lambda msg:
                           True if "sensor" in msg.sensor else False,
                           1)
        hwpc_filter.filter(lambda msg:
                           True if "test1" in msg.sensor else False,
                           2)
        hwpc_filter.filter(lambda msg:
                           True if msg.sensor == "sensor_test2" else False,
                           3)

        mongodb_it = iter(mongodb)
        for _ in range(2):
            hwpc_report = HWPCReport.deserialize(next(mongodb_it))
            assert hwpc_filter.route(hwpc_report) == [1, 2]

        for _ in range(2):
            hwpc_report = HWPCReport.deserialize(next(mongodb_it))
            assert hwpc_filter.route(hwpc_report) == [1, 3]

        for _ in range(2):
            hwpc_report = HWPCReport.deserialize(next(mongodb_it))
            assert hwpc_filter.route(hwpc_report) == [1]
