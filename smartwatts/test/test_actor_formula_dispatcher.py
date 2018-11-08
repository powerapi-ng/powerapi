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
