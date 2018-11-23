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

import pytest

from smartwatts.formula_dispatcher import ActorFormulaDispatcher
from smartwatts.group_by import AbstractGroupBy
from smartwatts.report import Report


class Report1(Report):
    """Fake Report class using for testing"""
    pass

class Report2(Report):
    """Fake Report class using for testing"""
    pass

class FakeGroupBy1(AbstractGroupBy):
    """Fake groupBy class using for testing"""
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A', 'B', 'C']

    def extract(self, report):
        return([(('a', 'b', 'c'), report)])


class FakeGroupBy2(AbstractGroupBy):
    """Fake groupBy class using for testing"""
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A', 'B', 'D']

    def extract(self, report):
        return([(('a', 'b', 'd'), report)])


def create_formula_dispatcher():
    """Create the formula dispatcher and initialize its group_by rules"""
    formula_dispatcher = ActorFormulaDispatcher('fd', None, None)
    formula_dispatcher.group_by(Report1, FakeGroupBy1(primary=True))
    formula_dispatcher.group_by(Report2, FakeGroupBy2())
    return formula_dispatcher


class TestPrivateMethods:
    """Test private method of ActorFormulaDispatcher"""

    def test_match_report_id_same_rule(self):
        """
        test if the function return the same id when the primary rule is also
        used to group by the current report
        """
        dispatcher = create_formula_dispatcher()
        initial_id = ('a', 'b', 'c')
        report_id = dispatcher._match_report_id(initial_id, FakeGroupBy1())
        assert report_id == initial_id

    def test_match_report_id_different_rules(self):
        """
        test if the function when FakeGroupBy1 is the primary rules on a report
        that use FakeGroupBy2 as group_by rule
        """
        dispatcher = create_formula_dispatcher()
        initial_id = ('a', 'b', 'd')
        report_id = dispatcher._match_report_id(initial_id, FakeGroupBy2())
        assert report_id == initial_id[:2]
