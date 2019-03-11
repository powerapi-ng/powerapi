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
from mock import Mock, patch
import mock

from powerapi.dispatcher import FormulaDispatcherReportHandler
from powerapi.dispatcher import DispatcherState, DispatcherActor
from powerapi.dispatcher import RouteTable
from powerapi.message import UnknowMessageTypeException
from powerapi.dispatch_rule import DispatchRule
from powerapi.report import Report, HWPCReport
from powerapi.database import MongoDB
from powerapi.actor import Actor, SocketInterface
from powerapi.dispatcher import StartHandler, NoPrimaryDispatchRuleRuleException
from powerapi.message import OKMessage, StartMessage, ErrorMessage


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


class DispatchRule1A(DispatchRule):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary)
        self.fields = ['A']

    def get_formula_id(self, report):
        return [(report.a,)]


class DispatchRule1AB(DispatchRule):
    """Group by rule that split the report if it contains a *b2* value

    if the report contain a *b2* value, it is spliten in two report the first
    one containing the *b* value and the second one containing the *b2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *b* value or the *b2 value of the
    report

    """
    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary)
        self.fields = ['A', 'B']

    def get_formula_id(self, report):
        b2_id = [] if report.b2 is None else [(report.a, report.b2)]
        return [(report.a, report.b)] + b2_id


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


class DispatchRule2A(DispatchRule):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary)
        self.fields = ['A']

    def get_formula_id(self, report):
        return [(report.a,)]


class DispatchRule2AC(DispatchRule):
    """Group by rule that split the report if it contains a *c2* value

    if the report contain a *c2* value, it is spliten in two report the first
    one containing the *c* value and the second one containing the *c2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *c* value or the *c2 value of the
    report

    """
    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary)
        self.fields = ['A', 'C']

    def get_formula_id(self, report):
        c2_ids = [] if report.c2 is None else [(report.a, report.c2)]
        return [(report.a, report.c)] + c2_ids


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

    def gen_test_get_formula_id(self, primary_dispatch_rule, dispatch_rule,
                                input_report, validation_id):
        """instanciate the handler whit given route table and primary dispatch
        rule, test if the handle function application on *input_report* return
        the same reports as in *validation_reports*

        """
        handler = FormulaDispatcherReportHandler()

        formula_ids = handler._extract_formula_id(input_report, dispatch_rule,
                                                  primary_dispatch_rule)
        formula_ids.sort()
        validation_id.sort()

        assert formula_ids == validation_id

    def test_get_formula_id_pgb_DispatchRule1A_gb_DispatchRule2A(self):
        """
        test get_formula_id function for a DispatchRule1A rule for Report1 as
        primary rule and DispatchRule2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [('a',)]
        - REPORT_2 : [('a',)]
        - REPORT_1_B2 : [('a',)]
        - REPORT_2_C2 : [('a',)]

        """
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule1A(),
                                     REPORT_1, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule2A(),
                                     REPORT_2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule1A(),
                                     REPORT_1_B2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule2A(),
                                     REPORT_2_C2, [('a',)])

    def test_get_formula_id_pgb_DispatchRule1A_gb_DispatchRule2AC(self):
        """test get_formula_id function for a DispatchRule1A rule for Report1 as
        primary rule and DispatchRule2AC rule for Report2

        ?????????

        Expected result for each input report :
        - REPORT_1 : [('a',)]
        - REPORT_2 : [('a',)]
        - REPORT_1_B2 : [('a',)]
        - REPORT_2_C2 : [('a',)]

        """
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule1A(),
                                     REPORT_1, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule2AC(),
                                     REPORT_2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule1A(),
                                     REPORT_1_B2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule2AC(),
                                     REPORT_2_C2, [('a',)])

    def test_get_formula_id_pgb_DispatchRule1AB_gb_DispatchRule2A(self):
        """
        test get_formula_id function for a DispatchRule1AB rule for Report1 as
        primary rule and DispatchRule2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [('a', 'b')]
        - REPORT_2 : [('a',)]
        - REPORT_1_B2 : [('a', 'b'), ('a', 'b2')]
        - REPORT_2_C2 : [('a',)]

        """
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule1AB(),
                                     REPORT_1, [('a', 'b')])
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule2A(),
                                     REPORT_2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule1AB(),
                                     REPORT_1_B2, [('a', 'b'), ('a', 'b2')])
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule2A(),
                                     REPORT_2_C2, [('a',)])

    def test_get_formula_id_pgb_DispatchRule1AB_gb_DispatchRule2AC(self):
        """
        test get_formula_id function for a DispatchRule1AB rule for Report1 as
        primary rule and DispatchRule2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [('a', 'b')]
        - REPORT_2 : [('a',)]
        - REPORT_1_B2 : [('a', 'b'), ('a', 'b2')]
        - REPORT_2_C2 : [('a',)]
        """
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule1AB(),
                                     REPORT_1, [('a', 'b')])
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule2AC(),
                                     REPORT_2, [('a',)])
        self.gen_test_get_formula_id(DispatchRule1AB(), DispatchRule1AB(),
                                     REPORT_1_B2, [('a', 'b'), ('a', 'b2')])
        self.gen_test_get_formula_id(DispatchRule1A(), DispatchRule2AC(),
                                     REPORT_2_C2, [('a',)])


def init_state():
    """ return a fresh dispatcher state """
    return DispatcherState(None, Mock(), Mock(),
                           lambda formula_id: Mock(),
                           RouteTable())


class TestHandlerFunction:
    """ Test Handle function of the dispatcher Handler """

    def test_empty_no_associated_dispatch_rule(self):
        """
        Test if an UnknowMessageTypeException is raised when using handle
        function on a report that is not associated with a dispatch_rule
        in the handler's route table

        """
        handler = FormulaDispatcherReportHandler()

        with pytest.raises(UnknowMessageTypeException):
            handler.handle(REPORT_1, init_state())

    def gen_test_handle(self, input_report, init_formula_id_list,
                        formula_id_validation_list, init_state):
        """instanciate the handler whit given route table and primary
        dispatchrule rule, test if the handle function return a state
        containing formula which their id are in formula_id_validation_list

        """
        init_state.route_table.dispatch_rule(Report1, DispatchRule1AB(True))
        init_state.route_table.dispatch_rule(Report2, DispatchRule2AC())
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
                                           Mock(),
                                           None, None)
        assert dispatcher_state.initialized is False

        # Define StartHandler
        start_handler = StartHandler()

        # Test Random message when state is not initialized
        to_send = [OKMessage(), ErrorMessage("Error"),
                   HWPCReport("test", "test", "test", {})]
        for msg in to_send:
            start_handler.handle(msg, dispatcher_state)
            assert fake_socket_interface.method_calls == []
            assert dispatcher_state.initialized is False

        # Try to initialize the state
        start_handler.handle(StartMessage(), dispatcher_state)
        assert dispatcher_state.initialized is True


##############################################################################

ACTOR_NAME = 'dispatcher_actor'


@patch('powerapi.actor.SocketInterface')
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

    gbr = DispatchRule1A(primary=True)
    route_table.dispatch_rule(Report1, gbr)
    dispatcher = DispatcherActor(ACTOR_NAME, Mock(), route_table)
    dispatcher.state.socket_interface = Mock()
    dispatcher.setup()
    return dispatcher


def test_actor_initialisation(dispatcher_actor):
    assert dispatcher_actor.state.alive is True


def test_actor_setup_without_dispatch_rule(dispatcher_actor):
    """ test to setup the dispatcher without seting a primary group by rule"""
    with pytest.raises(NoPrimaryDispatchRuleRuleException):
        dispatcher_actor.setup()


def test_actor_setup(initialized_dispatcher_actor):
    assert initialized_dispatcher_actor.state.route_table.primary_dispatch_rule is not None
