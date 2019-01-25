"""
Module dispatcher_test
"""

import pytest
from mock import Mock, patch
import mock

from smartwatts.dispatcher import FormulaDispatcherReportHandler
from smartwatts.dispatcher import DispatcherState, DispatcherActor
from smartwatts.dispatcher import RouteTable
from smartwatts.message import UnknowMessageTypeException
from smartwatts.group_by import GroupBy
from smartwatts.report import Report, HWPCReport
from smartwatts.database import MongoDB
from smartwatts.actor import Actor, SocketInterface
from smartwatts.dispatcher import StartHandler, NoPrimaryGroupByRuleException
from smartwatts.message import OKMessage, StartMessage, ErrorMessage


##############################################################################

def get_fake_socket_interface():
    """ Return a fake SockerInterface """
    return mock.Mock(spec_set=SocketInterface)


################################################################################

class Report1(Report):
    """ Fake report that can contain 2 or three values *a*, *b*, and *b2* """
    def __init__(self, a, b, b2=None):
        self.a = a
        self.b = b
        self.b2 = b2

    def __eq__(self, other):
        if not isinstance(other, Report1):
            return False
        return other.a == self.a and other.b == self.b and other.b2 == self.b2

    def __str__(self):
        return '(' + str(self.a) + ',' + (str(self.b)
                                          if self.b2 is None
                                          else ('(' + self.b + ',' + self.b2 +
                                                ')')) + ')'


class GroupBy1A(GroupBy):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        GroupBy.__init__(self, primary)
        self.fields = ['A']

    def extract(self, report):
        return [((report.a,), report)]


class GroupBy1AB(GroupBy):
    """Group by rule that split the report if it contains a *b2* value

    if the report contain a *b2* value, it is spliten in two report the first
    one containing the *b* value and the second one containing the *b2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *b* value or the *b2 value of the
    report

    """
    def __init__(self, primary=False):
        GroupBy.__init__(self, primary)
        self.fields = ['A', 'B']

    def extract(self, report):
        b2_report = [] if report.b2 is None else [
            ((report.a, report.b2), Report1(report.a, report.b2))
        ]
        return [((report.a, report.b), Report1(report.a, report.b))] + b2_report


class Report2(Report):
    """ Fake report that can contains two or three values : *a*, *c*, *c2* """
    def __init__(self, a, c, c2=None):
        self.a = a
        self.c = c
        self.c2 = c2

    def __eq__(self, other):
        if not isinstance(other, Report2):
            return False
        return other.a == self.a and other.c == self.c and other.c2 == self.c2

    def __str__(self):
        return '(' + str(self.a) + ',' + (str(self.c)
                                          if self.c2 is None
                                          else ('(' + self.c + ',' + self.c2 +
                                                ')')) + ')'
class GroupBy2A(GroupBy):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        GroupBy.__init__(self, primary)
        self.fields = ['A']

    def extract(self, report):
        return [((report.a,), report)]


class GroupBy2AC(GroupBy):
    """Group by rule that split the report if it contains a *c2* value

    if the report contain a *c2* value, it is spliten in two report the first
    one containing the *c* value and the second one containing the *c2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *c* value or the *c2 value of the
    report

    """
    def __init__(self, primary=False):
        GroupBy.__init__(self, primary)
        self.fields = ['A', 'C']

    def extract(self, report):
        c2_report = [] if report.c2 is None else [
            ((report.a, report.c2), Report2(report.a, report.c2))
        ]
        return [((report.a, report.c), Report2(report.a, report.c))] + c2_report


# Inputs reports
REPORT_1 = Report1('a', 'b')
REPORT_1_B2 = Report1('a', 'b', 'b2')
REPORT_2 = Report2('a', 'c')
REPORT_2_C2 = Report2('a', 'c', 'c2')

# Report that could be return by the handle function
SPLITED_REPORT_1_B2 = Report1('a', 'b2')
SPLITED_REPORT_2_C2 = Report2('a', 'c2')


class TestExtractReportFunction:
    """Test handle function of the formula dispatcher handler

        The first test case test empty route table rule

        The other function test name describe the initial test of the handler
        before to use its handle function. It is writen like this :
        test_handle_pgb_PRIMARY_GROUPBY_RULE_CLASSE_gb_OTHER_GROUPBY_RULE_CLASS

        For each of theses functions, we test the result of handle function on 4
        predefinded reports defined below as constants.

    """

    def gen_test_extract_report(self, primary_group_by_rule, group_by_rule,
                                input_report, validation_reports):
        """instanciate the handler whit given route table and primary groupby
        rule, test if the handle function application on *input_report* return
        the same reports as in *validation_reports*

        """
        handler = FormulaDispatcherReportHandler()

        result_reports = handler._extract_reports(input_report, group_by_rule,
                                                  primary_group_by_rule)
        result_reports.sort(key=lambda result_tuple: result_tuple[0])
        validation_reports.sort(key=lambda result_tuple: result_tuple[0])

        assert result_reports == validation_reports

    def test_extract_report_pgb_GroupBy1A_gb_GroupBy2A(self):
        """
        test extract_report function for a GroupBy1A rule for Report1 as
        primary rule and GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a',), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a',), REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2_C2)]

        """
        self.gen_test_extract_report(GroupBy1A(), GroupBy1A(), REPORT_1,
                                     [(('a',), REPORT_1)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy2A(), REPORT_2,
                                     [(('a',), REPORT_2)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy1A(), REPORT_1_B2,
                                     [(('a',), REPORT_1_B2)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy2A(), REPORT_2_C2,
                                     [(('a',), REPORT_2_C2)])

    def test_extract_report_pgb_GroupBy1A_gb_GroupBy2AC(self):
        """test extract_report function for a GroupBy1A rule for Report1 as
        primary rule and GroupBy2AC rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a',), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a',), REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2),
                         (('a',), SPLITED_REPORT_2_C2)]

        """
        self.gen_test_extract_report(GroupBy1A(), GroupBy1A(), REPORT_1,
                                     [(('a',), REPORT_1)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy2AC(), REPORT_2,
                                     [(('a',), REPORT_2)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy1A(), REPORT_1_B2,
                                     [(('a',), REPORT_1_B2)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy2AC(), REPORT_2_C2,
                                     [(('a',), REPORT_2),
                                      (('a',), SPLITED_REPORT_2_C2)])

    def test_extract_report_pgb_GroupBy1AB_gb_GroupBy2A(self):
        """
        test extract_report function for a GroupBy1AB rule for Report1 as
        primary rule and GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a', 'b'), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a', 'b'), REPORT_1_B2),
                         (('a', 'b2'), SPLITED_REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2_C2)]

        """
        self.gen_test_extract_report(GroupBy1AB(), GroupBy1AB(), REPORT_1,
                                     [(('a', 'b'), REPORT_1)])
        self.gen_test_extract_report(GroupBy1AB(), GroupBy2A(), REPORT_2,
                                     [(('a',), REPORT_2)])
        self.gen_test_extract_report(GroupBy1AB(), GroupBy1AB(), REPORT_1_B2,
                                     [(('a', 'b'), REPORT_1),
                                      (('a', 'b2'), SPLITED_REPORT_1_B2)])
        self.gen_test_extract_report(GroupBy1AB(), GroupBy2A(), REPORT_2_C2,
                                     [(('a',), REPORT_2_C2)])

    def test_extract_report_pgb_GroupBy1AB_gb_GroupBy2AC(self):
        """
        test extract_report function for a GroupBy1AB rule for Report1 as
        primary rule and GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a', 'b'), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a', 'b'), REPORT_1_B2),
                         (('a', 'b2'), SPLITED_REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2),
                         (('a',), SPLITED_REPORT_2_C2)]
        """
        self.gen_test_extract_report(GroupBy1AB(), GroupBy1AB(), REPORT_1,
                                     [(('a', 'b'), REPORT_1)])
        self.gen_test_extract_report(GroupBy1AB(), GroupBy2AC(), REPORT_2,
                                     [(('a',), REPORT_2)])
        self.gen_test_extract_report(GroupBy1AB(), GroupBy1AB(), REPORT_1_B2,
                                     [(('a', 'b'), REPORT_1),
                                      (('a', 'b2'), SPLITED_REPORT_1_B2)])
        self.gen_test_extract_report(GroupBy1A(), GroupBy2AC(), REPORT_2_C2,
                                     [(('a',), REPORT_2),
                                      (('a',), SPLITED_REPORT_2_C2)])


def init_state():
    """ return a fresh dispatcher state """
    return DispatcherState(None, Mock(), lambda formula_id, context: Mock(),
                           RouteTable())


class TestHandlerFunction:
    """ Test Handle function of the dispatcher Handler """

    def test_empty_no_associated_group_by_rule(self):
        """
        Test if an UnknowMessageTypeException is raised when using handle
        function on a report that is not associated with a group_by rule in the
        handler's route table

        """
        handler = FormulaDispatcherReportHandler()

        with pytest.raises(UnknowMessageTypeException):
            handler.handle(REPORT_1, init_state())

    def gen_test_handle(self, input_report, init_formula_id_list,
                        formula_id_validation_list, init_state):
        """instanciate the handler whit given route table and primary groupby
        rule, test if the handle function return a state containing formula
        which their id are in formula_id_validation_list

        """
        init_state.route_table.group_by(Report1, GroupBy1AB(True))
        init_state.route_table.group_by(Report2, GroupBy2AC())
        handler = FormulaDispatcherReportHandler()

        for formula_id in init_formula_id_list:
            init_state.add_formula(formula_id)

        result_state = handler.handle(input_report, init_state)
        formula_id_result_list = list(map(lambda x: x[0],
                                          result_state.get_all_formula()))
        formula_id_result_list.sort(key=lambda result_tuple: result_tuple[0])

        formula_id_result_list.sort()
        formula_id_validation_list.sort()
        assert formula_id_result_list == formula_id_validation_list

    def test_handler_with_no_init_formula(self):
        """
        Test the Handler with no formula in the initial state

        Expected formula id that the returned state must contain
        - REPORT_1 : [('a', 'b')]
        - SPLITED_REPORT_1_B2 :  [('a', 'b2')]
        - REPORT_2 : []
        """
        init_formula_id_list = []
        self.gen_test_handle(REPORT_1, init_formula_id_list, [('a', 'b')],
                             init_state())

        self.gen_test_handle(SPLITED_REPORT_1_B2, init_formula_id_list,
                             [('a', 'b2')], init_state())

        self.gen_test_handle(REPORT_2, init_formula_id_list, [], init_state())

    def test_handler_with_one_init_formula(self):
        """
        Test the Handler with a formula ('a', 'b') in the initial state

        Expected formula id that the returned state must contain
        - REPORT_1 : [('a', 'b')]
        - SPLITED_REPORT_1_B2 :  [('a', 'b'), ('a', 'b2')]
        - REPORT_2 :  [('a', 'b')]

        """
        init_formula_id_list = [('a', 'b')]
        self.gen_test_handle(REPORT_1, init_formula_id_list, [('a', 'b')],
                             init_state())

        self.gen_test_handle(SPLITED_REPORT_1_B2, init_formula_id_list,
                             [('a', 'b'), ('a', 'b2')], init_state())

        self.gen_test_handle(REPORT_2, init_formula_id_list, [('a', 'b')],
                             init_state())

    def test_handler_with_two_init_formula(self):
        """
        Test the Handler with two formula : ('a', 'b') and ('a', 'b2') in the
        initial state

        Expected formula id that the returned state must contain
        - REPORT_1 : [('a', 'b'), ('a', 'b2')]
        - SPLITED_REPORT_1_B2 : [('a', 'b'), ('a', 'b2')]
        - REPORT_2 : [('a', 'b'), ('a', 'b2')]

        """
        init_formula_id_list = [('a', 'b'), ('a', 'b2')]
        self.gen_test_handle(REPORT_1, init_formula_id_list,
                             init_formula_id_list, init_state())

        self.gen_test_handle(SPLITED_REPORT_1_B2, init_formula_id_list,
                             init_formula_id_list, init_state())

        self.gen_test_handle(REPORT_2, init_formula_id_list,
                             init_formula_id_list, init_state())

    def test_dispatcher_start_handler(self):
        """
        Test the StartHandler of DispatcherActor
        """

        # Define DispatcherState
        fake_socket_interface = get_fake_socket_interface()
        dispatcher_state = DispatcherState(Actor._initial_behaviour,
                                           fake_socket_interface,
                                           None, None)
        assert dispatcher_state.initialized is False

        # Define StartHandler
        start_handler = StartHandler()

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   HWPCReport("test", "test", "test")]
        for msg in to_send:
            start_handler.handle(msg, dispatcher_state)
            assert fake_socket_interface.method_calls == []
            assert dispatcher_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage(), dispatcher_state)
        assert dispatcher_state.initialized is True


##############################################################################

ACTOR_NAME = 'dispatcher_actor'

@patch('smartwatts.actor.SocketInterface')
@pytest.fixture()
def dispatcher_actor():
    """ return an uninitialized actor """
    dispatcher = DispatcherActor(ACTOR_NAME, Mock(), RouteTable())
    dispatcher.state.socket_interface = Mock()
    return dispatcher


@pytest.fixture()
def initialized_dispatcher_actor():
    """ return an uninitialized actor """
    route_table = RouteTable()

    gbr = GroupBy1A(primary=True)
    route_table.group_by(Report1, gbr)
    dispatcher = DispatcherActor(ACTOR_NAME, Mock(), route_table)
    dispatcher.state.socket_interface = Mock()
    dispatcher.setup()
    return dispatcher


def test_actor_initialisation(dispatcher_actor):
    assert dispatcher_actor.state.alive is True


def test_actor_setup_without_group_by(dispatcher_actor):
    """ test to setup the dispatcher without seting a primary group by rule"""
    with pytest.raises(NoPrimaryGroupByRuleException):
        dispatcher_actor.setup()


def test_actor_setup(initialized_dispatcher_actor):
    assert initialized_dispatcher_actor.state.route_table.primary_group_by_rule is not None
