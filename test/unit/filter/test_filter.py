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

"""
Module test_filter
"""

import pytest
from powerapi.filter import Filter, FilterUselessError
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel
from powerapi.database import MongoDB


class TestFilter:

    def test_without_filter(self):
        """ Test filter without any filter, raise an error """
        hwpc_filter = Filter()
        with pytest.raises(FilterUselessError) as pytest_wrapped:
            hwpc_filter.route(HWPCReport())
        assert pytest_wrapped.type == FilterUselessError


    def test_with_two_filter(self):
        """
        Test filter with two filter
        - 2 first report return first dispatcher
        - 2 next report return first and second dispatcher
        - 2 next report return None
        """
        mongodb = MongoDB("localhost", 27017, "test_filter",
                          "test_filter1", report_model=HWPCModel())
        mongodb.load()
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
        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) == [1, 2]

        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) == [1, 3]

        for _ in range(2):
            hwpc_report = HWPCReport()
            hwpc_report.deserialize(mongodb.get_next())
            assert hwpc_filter.route(hwpc_report) == [1]
