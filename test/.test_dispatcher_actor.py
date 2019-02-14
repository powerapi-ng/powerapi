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

import time
import pytest
import zmq

from powerapi.dispatcher import DispatcherActor
from powerapi.group_by import AbstractGroupBy
from powerapi.report import Report
from powerapi.test.mocked_formula import MockedFormula
# from powerapi.report import HWPCReport
# from powerapi.group_by import HWPCGroupBy, HWPCDepthLevel


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
    formula_dispatcher = DispatcherActor('fd', None, None)
    formula_dispatcher.group_by(Report1, FakeGroupBy1(primary=True))
    formula_dispatcher.group_by(Report2, FakeGroupBy2())
    return formula_dispatcher


class TestGroupBy:
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


@pytest.fixture(scope='module')
def message_interceptor():
    """ Initialize the message interceptor for all the test module"""
    return MessageInterceptor()

@pytest.fixture
def formula_dispatcher(request, message_interceptor):
    """Initialize the formula dispatcher

    The formula dispatcher is reinitialized for each test function

    It use the group_by rule contained in group_by_list attribute of the test
    class used

    """
    dispatcher = DispatcherActor('fd', lambda name, verbose:
                                 MockedFormula(name, message_interceptor, verbose=verbose),
                                 verbose=True)

    group_by_list = getattr(request.instance, 'group_by_list', None)
    for report_class, group_by_rule in group_by_list:
        dispatcher.group_by(report_class, group_by_rule)

    context = zmq.Context()
    dispatcher.start()
    dispatcher.connect(context)
    yield dispatcher
    dispatcher.kill()
    message_interceptor.clear_message()
    time.sleep(0.2)

@pytest.fixture
def create_formulas(message_interceptor, formula_dispatcher):
    """Create formula and consume creation message received after their creation
    """
    formula_dispatcher.send(Report1())
    msg = message_interceptor.receive(1000)
    print(msg)
    time.sleep(0.2)

class TestGroupByROOT:
    # ((report_class, group_by_rule, primary_bool)]
    group_by_list = [(Report1, FakeGroupBy1(primary=True))]

    def test_no_creation_for_random_msg(self, message_interceptor, formula_dispatcher):
        formula_dispatcher.send("toto")
        assert message_interceptor.receive(300) == None
        assert False

    def test_creation_after_send_one_report(self, message_interceptor, formula_dispatcher):
        formula_dispatcher.send(Report1())
        msg = message_interceptor.receive(300)
        assert isinstance(msg, CreationMessage)

    def test_send_random_msg(self, message_interceptor, formula_dispatcher, create_formulas):
        formula_dispatcher.send("toto")
        assert message_interceptor.receive(300) == None
