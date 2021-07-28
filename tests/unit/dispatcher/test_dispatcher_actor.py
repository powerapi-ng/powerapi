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

from thespian.actors import ActorExitRequest

from powerapi.test_utils.actor import is_actor_alive, system
from powerapi.test_utils.dummy_actor import DummyActor, DummyFormulaActor, CrashInitFormulaActor, CrashFormulaActor, DummyStartMessage, logger, LOGGER_NAME
from powerapi.test_utils.abstract_test import AbstractTestActor, recv_from_pipe
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.dispatcher.dispatcher_actor import _extract_formula_id
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel, DispatchRule
from powerapi.dispatch_rule import PowerDispatchRule, PowerDepthLevel
from powerapi.message import OKMessage, ErrorMessage, DispatcherStartMessage, StartMessage, FormulaStartMessage, EndMessage
from powerapi.formula import FormulaValues
from powerapi.dispatch_rule import DispatchRule
from powerapi.report import Report, HWPCReport, PowerReport
from powerapi.database import MongoDB

def define_dispatch_rules(rules):
    def wrap(func):
        setattr(func, '_dispatch_rules', rules)
        return func
    return wrap


def define_formula_class(formula_class):
    """
    A decorator to set the _formula_class
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_formula_class', formula_class)
        return func
    return wrap


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the dispatch_rules fixtures in test environement with collected the
    value _dispatch_rules if it exist or with an empty dispatch_rules

    :param metafunc: the test context given by pytest
    """
    if 'dispatch_rules' in metafunc.fixturenames:
        dispatch_rules = getattr(metafunc.function, '_dispatch_rules', None)
        if isinstance(dispatch_rules, list):
            metafunc.parametrize('dispatch_rules', [dispatch_rules])
        else:
            metafunc.parametrize('dispatch_rules', [[(Report1, DispatchRule1AB(primary=True))]])
    if 'formula_class' in metafunc.fixturenames:
        formula_class = getattr(metafunc.function, '_formula_class', DummyFormulaActor)
        metafunc.parametrize('formula_class', [formula_class])


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

    def __repr__(self):
        return self.__str__()


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

    def __repr__(self):
        return self.__str__()


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


class Report3(Report):
    """ Fake report that contains same values as Report 1 and an other value"""
    def __init__(self, a, b, d):
        self.a = a
        self.b = b
        self.d = d
        

    def __eq__(self, other):
        if not isinstance(other, Report3):
            return False
        return other.a == self.a and other.b == self.b and other.d == self.d

    def __str__(self):
        return '(' + str(self.a) + ',' + str(self.b) + ',' + str(self.d) + ')'

    def __repr__(self):
        return self.__str__()


class DispatchRule3(DispatchRule):
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
        return [(report.a, report.b)]


# Inputs reports
REPORT_1 = Report1('a', 'b')
REPORT_1_B2 = Report1('a', 'b', 'b2')
REPORT_2 = Report2('a', 'c')
REPORT_2_C2 = Report2('a', 'c', 'c2')
REPORT_3 = Report3('a', 'b', 'd')
                                                               

# Report that could be return by the handle function
SPLITED_REPORT_1_B2 = Report1('a', 'b2')
SPLITED_REPORT_2_C2 = Report2('a', 'c2')


class TestDispatcher(AbstractTestActor):

    @pytest.fixture
    def actor(self, system):
        actor = system.createActor(DispatcherActor)
        yield actor
        system.tell(actor, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, dispatch_rules, logger, formula_class):
        route_table = RouteTable()
        for report_type, gbr in dispatch_rules:
            route_table.dispatch_rule(report_type, gbr)
        values = FormulaValues({'fake_pusher': LOGGER_NAME})
        return DispatcherStartMessage('system', 'dispatcher', formula_class, values, route_table, 'test_device')

    @pytest.fixture
    def dispatcher_with_formula(self, system, started_actor, logger, dispatch_rules, dummy_pipe_out):
        system.tell(started_actor, REPORT_1)
        recv_from_pipe(dummy_pipe_out, 0.5)
        recv_from_pipe(dummy_pipe_out, 0.5)
        return started_actor

    @pytest.fixture
    def dispatcher_with_two_formula(self, system, dispatcher_with_formula, logger, dispatch_rules, dummy_pipe_out):
        system.tell(dispatcher_with_formula, Report1('a', 'c'))
        recv_from_pipe(dummy_pipe_out, 0.5)
        recv_from_pipe(dummy_pipe_out, 0.5)
        return dispatcher_with_formula

    @define_dispatch_rules([(Report1, DispatchRule1A(primary=True))])
    def test_starting_actor_without_DispatcherStartMessage_must_answer_error_message(self, system, actor, logger):
        answer = system.ask(actor, StartMessage('system', 'test'))
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'use DispatcherStartMessage instead of StartMessage'

    @define_dispatch_rules([(Report2, DispatchRule2A(primary=True))])
    def test_send_Report1_without_dispatch_rule_for_Report1_keep_dispatcher_alive(self, system, started_actor, logger):
        system.tell(started_actor, REPORT_1)
        assert is_actor_alive(system, started_actor)

    @define_dispatch_rules([(Report2, DispatchRule2A(primary=True))])
    def test_send_Report1_without_dispatch_rule_for_Report1_dont_create_formula(self, system, started_actor, logger, dummy_pipe_out):
        system.tell(started_actor, REPORT_1)
        assert recv_from_pipe(dummy_pipe_out, 0.5) is None

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_Report1_with_dispatch_rule_for_Report1_and_no_formula_created_must_create_a_new_formula(self, system, started_actor, dummy_pipe_out):
        system.tell(started_actor, REPORT_1)
        _, start_msg =  recv_from_pipe(dummy_pipe_out, 0.5)
        assert isinstance(start_msg, StartMessage)
        assert start_msg.name == "('dispatcher', 'a', 'b')"

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_Report1_with_dispatch_rule_for_Report1_and_one_formula_forward_report_to_formula(self, system, dispatcher_with_formula, logger, dummy_pipe_out):
        system.tell(dispatcher_with_formula, REPORT_1)
        _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
        assert msg == REPORT_1
        assert recv_from_pipe(dummy_pipe_out, 0.5) is None

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True)),
                            (Report2, DispatchRule2A())])
    def test_send_Report2_with_dispatch_rule_for_Report1_Primary_and_two_formula_forward_report_to_all_formula(self, system, dispatcher_with_two_formula, dummy_pipe_out):
        system.tell(dispatcher_with_two_formula, REPORT_2)
        _, msg1 = recv_from_pipe(dummy_pipe_out, 0.5)
        _, msg2 = recv_from_pipe(dummy_pipe_out, 0.5)

        assert msg1 == REPORT_2
        assert msg2 == REPORT_2

        assert recv_from_pipe(dummy_pipe_out, 0.5) is None

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_REPORT1_B2_with_dispatch_rule_1AB_must_create_two_formula(self, system, started_actor, dummy_pipe_out):
        system.tell(started_actor, REPORT_1_B2)
        start_message = []
        reports = []

        for _ in range(4):
            _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
            if isinstance(msg, StartMessage):
                start_message.append(msg)
            if isinstance(msg, Report):
                reports.append(msg)

        assert len(reports) == 2
        assert len(start_message) == 2

        for msg in start_message:
            assert msg.name == "('dispatcher', 'a', 'b')" or msg.name == "('dispatcher', 'a', 'b2')"

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True)),
                            (Report3, DispatchRule3())])
    def test_send_REPORT3_on_dispatcher_with_two_formula_and_dispatch_rule_1AB_send_report_to_one_formula(self, system, started_actor, dummy_pipe_out):
        system.tell(started_actor, REPORT_1_B2)
        start_message = []
        reports = []

        for _ in range(4):
            _, msg = recv_from_pipe(dummy_pipe_out, 0.5)

        print('=========================================')
        system.tell(started_actor, REPORT_3)
        _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
        assert msg == REPORT_3
        assert recv_from_pipe(dummy_pipe_out, 0.5) is None

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_ActorExitRequest_make_dispatcher_forward_it_to_formula(self, system, dispatcher_with_two_formula, logger, dummy_pipe_out):
        system.tell(dispatcher_with_two_formula, ActorExitRequest())

        _, msg1 = recv_from_pipe(dummy_pipe_out, 0.5)
        _, msg2 = recv_from_pipe(dummy_pipe_out, 0.5)

        assert msg1 == 'dead'
        assert msg2 == 'dead'

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    @define_formula_class(CrashFormulaActor)
    def test_send_report_to_a_dispatcher_with_crashed_formula_must_restart_formula(self, system, dispatcher_with_formula, dummy_pipe_out):
        # make formula crash
        system.tell(dispatcher_with_formula, REPORT_1)
        b, a = recv_from_pipe(dummy_pipe_out, 0.5)
        print('1' +str((b,a)))
        system.tell(dispatcher_with_formula, REPORT_1)
        _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
        assert msg == 'crash'

        # test if formula was restarted
        system.tell(dispatcher_with_formula, REPORT_1)
        _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
        assert msg == REPORT_1

    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True)),
                            (Report2, DispatchRule2A())])
    def test_send_EndMessage_to_dispatcher_with_two_formula_must_forward_it_to_all_formula(self, system, dispatcher_with_two_formula, dummy_pipe_out):
        system.tell(dispatcher_with_two_formula, EndMessage('system'))
        end_messages = 0
        for _ in range(2):
            _, msg = recv_from_pipe(dummy_pipe_out, 2)
            assert isinstance(msg, EndMessage)

    @define_dispatch_rules([(Report1, DispatchRule1A(primary=True))])
    def test_dispatcher_that_start_formula_crashing_at_initialization_musnt_forward_report_to_this_formula(self, system, dispatch_rules, actor, logger, dummy_pipe_out):

        route_table = RouteTable()
        for report_type, gbr in dispatch_rules:
            route_table.dispatch_rule(report_type, gbr)
        values = FormulaValues({'fake_pusher': LOGGER_NAME})
        start_message =  DispatcherStartMessage('system', 'dispatcher', CrashInitFormulaActor, values, route_table, 'test_device')
        system.ask(actor, start_message)
        system.tell(actor, REPORT_1)
        assert recv_from_pipe(dummy_pipe_out, 0.5) is None


#############################################
# TEST METIER DE L'EXTRACTION DU FORMULA ID #
#############################################
#                                           #
# PGB = Primary group by rule               #
# GB = group by rule                        #
#                                           #
#############################################
def gen_test_extract_formula_id(primary_dispatch_rule, dispatch_rule, input_report, validation_id):
    """
    generate a test with that extract a formula id from an input report with a given dispatch rule and a primary dispatch rules
    test if the extracted formula_ids are the same that given validation report ids
    """
    formula_ids = _extract_formula_id(input_report, dispatch_rule, primary_dispatch_rule)
    formula_ids.sort()
    validation_id.sort()
    assert formula_ids == validation_id


def test_extract_formula_id_with_pgb_DispatchRule1A_on_REPORT_1_must_return_good_formula_id():
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, pgb, REPORT_1, [('a',)])
    gen_test_extract_formula_id(pgb, pgb, REPORT_1_B2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1A_gb_DispatchRule2A_on_REPORT_2_must_return_good_formula_id():
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1A_gb_DispatchRule2AC_on_REPORT_2_must_return_good_formula_id():
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1AB_on_REPORT_1_must_return_good_formula_id():
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, pgb, REPORT_1, [('a', 'b')])
    gen_test_extract_formula_id(pgb, pgb, REPORT_1_B2, [('a', 'b'), ('a', 'b2')])

def test_extract_formula_id_with_pgb_DispatchRule1AB_gb_DispatchRule2A_on_REPORT_2_must_return_good_formula_id():
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1AB_gb_DispatchRule2AC_on_REPORT_2_must_return_good_formula_id():
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2_C2, [('a',)])
