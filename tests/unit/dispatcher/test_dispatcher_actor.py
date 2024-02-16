# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
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

from datetime import datetime
from time import sleep

import pytest

from powerapi.dispatch_rule import DispatchRule
from powerapi.dispatcher import DispatcherActor, RouteTable, extract_formula_id
from powerapi.message import PoisonPillMessage
from powerapi.report import Report, HWPCReport, PowerReport

from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe, is_actor_alive, \
    PUSHER_NAME_POWER_REPORT

from tests.utils.formula.dummy import DummyFormulaActor


def define_dispatch_rules(rules):
    """
        Return a wrap function with dispatch rules by using the given rules
        :param rules: The rules to be applied
    """

    def wrap(func):
        setattr(func, '_dispatch_rules', rules)
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
    """
        Fake report that can contain 2 or three values *a*, *b*, and *b2*
    """

    def __init__(self, a, b, b2=None, timestamp=datetime.now(), sensor='test_sensor', target='test_target'):
        Report.__init__(self, timestamp=timestamp, target=target, sensor=sensor)
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
                                          else ('(' + str(self.b) + ',' + str(self.b2) +
                                                ')')) + ')'

    def __repr__(self):
        return self.__str__()


class DispatchRule1A(DispatchRule):
    """
        Group by rule that return the received report its id is the report *a* value

    """

    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary, ['A'])

    def get_formula_id(self, report):
        return [(report.a,)]


class DispatchRule1AB(DispatchRule):
    """
        Group by rule that split the report if it contains a *b2* value

        if the report contain a *b2* value, it is split in two report the first
        one containing the *b* value and the second one containing the *b2* value

        sub-report identifier is a tuple of two values, the first one is the *a*
        value of the report, the second one is the *b* value or the *b2 value of the
        report

    """

    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary, ['A', 'B'])

    def get_formula_id(self, report):
        b2_id = [] if report.b2 is None else [(report.a, report.b2)]
        return [(report.a, report.b)] + b2_id


class Report2(Report):
    """
        Fake report that can contains two or three values : *a*, *c*, *c2*
    """

    def __init__(self, a, c, c2=None, timestamp=datetime.now(), sensor='test_sensor', target='test_target'):
        Report.__init__(self, timestamp=timestamp, target=target, sensor=sensor)
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
    """
        Group by rule that return the received report its id is the report *a* value

    """

    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary, ['A'])

    def get_formula_id(self, report):
        return [(report.a,)]


class DispatchRule2AC(DispatchRule):
    """
        Group by rule that split the report if it contains a *c2* value

        if the report contain a *c2* value, it is split in two report the first
        one containing the *c* value and the second one containing the *c2* value

        sub-report identifier is a tuple of two values, the first one is the *a*
        value of the report, the second one is the *c* value or the *c2 value of the
        report
    """

    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary, ['A', 'C'])

    def get_formula_id(self, report):
        c2_ids = [] if report.c2 is None else [(report.a, report.c2)]
        return [(report.a, report.c)] + c2_ids


class Report3(Report):
    """
        Fake report that contains same values as Report 1 and an other value
    """

    def __init__(self, a, b, d, timestamp=datetime.now(), sensor='test_sensor', target='test_target'):
        Report.__init__(self, timestamp=timestamp, target=target, sensor=sensor)
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
    """
        Group by rule that split the report if it contains a *b2* value

        if the report contain a *b2* value, it is spliten in two report the first
        one containing the *b* value and the second one containing the *b2* value

        sub-report identifier is a tuple of two values, the first one is the *a*
        value of the report, the second one is the *b* value or the *b2 value of the
        report

    """

    def __init__(self, primary=False):
        DispatchRule.__init__(self, primary, ['A', 'B'])

    def get_formula_id(self, report):
        return [(report.a, report.b)]


# Input reports
REPORT_1 = Report1('a', 'b')
REPORT_1_B2 = Report1('a', 'b', 'b2')
REPORT_2 = Report2('a', 'c')
REPORT_2_C2 = Report2('a', 'c', 'c2')
REPORT_3 = Report3('a', 'b', 'd')

# Report that could be return by the handle function
SPLITED_REPORT_1_B2 = Report1('a', 'b2')
SPLITED_REPORT_2_C2 = Report2('a', 'c2')

REPORT_TYPE_TO_BE_SENT = Report1
REPORT_TYPE_TO_BE_SENT_2 = HWPCReport


class TestDispatcher(AbstractTestActor):
    """
        Class for testing DispatcherActor
    """

    @staticmethod
    @pytest.fixture
    def formula_class():
        """
            Return the formula class that will be used for
        """
        return lambda name, pushers: DummyFormulaActor(name=name, pushers=pushers, socket=0, core=0)

    @pytest.fixture
    def actor(self, dispatch_rules=None, started_fake_pusher_power_report=None):

        route_table = RouteTable()
        for report_type, gbr in dispatch_rules:
            route_table.dispatch_rule(report_type, gbr)
        actor = DispatcherActor(name='test-dispatcher',
                                formula_init_function=lambda name, pushers: DummyFormulaActor(name=name,
                                                                                              pushers=pushers, socket=0,
                                                                                              core=0),
                                route_table=route_table,
                                pushers={PUSHER_NAME_POWER_REPORT: started_fake_pusher_power_report})

        return actor

    @staticmethod
    @pytest.fixture
    def dispatcher_with_formula(started_actor, dummy_pipe_out):
        """
            Send a report to force the creation of a formula in a started DispatcherActor.
            The actor with the created formula is returned
        """
        started_actor.send_data(REPORT_1)
        recv_from_pipe(dummy_pipe_out, 0.5)
        recv_from_pipe(dummy_pipe_out, 0.5)
        return started_actor

    @staticmethod
    @pytest.fixture
    def dispatcher_with_two_formula(dispatcher_with_formula, dummy_pipe_out):
        """
            Send a report to force the creation of a formula in a DispatcherActor that already has a formula.
            The actor with two formulas is returned
        """
        dispatcher_with_formula.send_data(Report1('a', 'c'))
        recv_from_pipe(dummy_pipe_out, 0.5)
        recv_from_pipe(dummy_pipe_out, 0.5)
        return dispatcher_with_formula

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    @define_dispatch_rules([(Report2, DispatchRule2A(primary=True))])
    def test_send_Report1_without_dispatch_rule_for_Report1_stop_dispatcher(started_actor):
        """
            Check that dispatcher stops when it receives a report that it can no deal with it.
        """
        started_actor.send_data(REPORT_1)
        assert not is_actor_alive(started_actor)

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    @define_dispatch_rules([(Report2, DispatchRule2A(primary=True))])
    def test_send_Report1_without_dispatch_rule_for_Report1_dont_create_formula(started_actor, dummy_pipe_out):

        """
            Check that a formula is no created by DispatcherActor when it does not have a rule to deal with
            a given report type
        """
        started_actor.send_data(REPORT_1)
        assert recv_from_pipe(dummy_pipe_out, 0.5) == (None, None)
        assert len(started_actor.state.formula_dict) == 0

    @staticmethod
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_Report1_with_dispatch_rule_for_Report1_and_no_formula_created_must_create_a_new_formula(started_actor, dummy_pipe_out):
        """
            Check that a formula is created when a report is received
        """
        started_actor.send_data(REPORT_1)
        _, power_report = recv_from_pipe(dummy_pipe_out, 0.2)
        assert isinstance(power_report, PowerReport)
        assert power_report.power == 42

    @staticmethod
    @pytest.mark.usefixtures("shutdown_system")
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_Report1_with_dispatch_rule_for_Report1_and_one_formula_send_report_to_formula(dispatcher_with_formula, dummy_pipe_out):
        """
            Check that DispatcherActor with a created formula sent a report to it
        """
        expected_metadata = {'formula_name': "('" + dispatcher_with_formula.name + "', '" + REPORT_1.a + "', '" +
                                             REPORT_1.b + "')",
                             'socket': 0}

        expected_report = PowerReport(timestamp=REPORT_1.timestamp, power=42, sensor=REPORT_1.sensor,
                                      target=REPORT_1.target, metadata=expected_metadata)
        dispatcher_with_formula.send_data(REPORT_1)
        _, msg = recv_from_pipe(dummy_pipe_out, 0.5)

        assert msg == expected_report
        assert recv_from_pipe(dummy_pipe_out, 0.5) == (None, None)

    @staticmethod
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True)), (Report2, DispatchRule2A())])
    def test_send_Report2_with_dispatch_rule_for_Report1_Primary_and_two_formula_send_report_to_all_formula(dispatcher_with_two_formula, dummy_pipe_out):
        """
            Check that DispatcherActor sent a report to all existing formulas
        """
        metadata_b = {'formula_name': "('" + dispatcher_with_two_formula.state.actor.name + "', 'a', 'b')",
                      'socket': 0}
        expected_report_b = PowerReport(timestamp=REPORT_2.timestamp, sensor=REPORT_2.sensor, target=REPORT_2.target,
                                        power=42, metadata=metadata_b)

        metadata_c = {'formula_name': "('" + dispatcher_with_two_formula.state.actor.name + "', 'a', 'c')",
                      'socket': 0}
        expected_report_c = PowerReport(timestamp=REPORT_2.timestamp, sensor=REPORT_2.sensor, target=REPORT_2.target,
                                        power=42, metadata=metadata_c)

        dispatcher_with_two_formula.send_data(REPORT_2)
        _, msg1 = recv_from_pipe(dummy_pipe_out, 0.5)
        _, msg2 = recv_from_pipe(dummy_pipe_out, 0.5)

        assert msg1 in [expected_report_b, expected_report_c]
        assert msg2 in [expected_report_b, expected_report_c]

        assert recv_from_pipe(dummy_pipe_out, 0.5) == (None, None)

    @staticmethod
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_REPORT1_B2_with_dispatch_rule_1AB_must_create_two_formula(started_actor, dummy_pipe_out):
        """
            Check that two formulas are created by DispatcherActor
        """
        started_actor.send_data(REPORT_1_B2)
        reports = []

        for _ in range(2):
            _, msg = recv_from_pipe(dummy_pipe_out, 0.5)
            reports.append(msg)

        assert len(reports) == 2

    @staticmethod
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True)), (Report3, DispatchRule3())])
    def test_send_REPORT3_on_dispatcher_with_two_formula_and_dispatch_rule_1AB_send_report_to_one_formula(dispatcher_with_two_formula, dummy_pipe_out):
        """
            Check that 3 reports are produced by formulas when DispatcherActor receives
        """

        metadata_b = {'formula_name': "('" + dispatcher_with_two_formula.state.actor.name + "', 'a', 'b')",
                      'socket': 0}

        expected_report_b_report_3 = PowerReport(timestamp=REPORT_3.timestamp, sensor=REPORT_3.sensor,
                                                 target=REPORT_3.target, power=42, metadata=metadata_b)

        dispatcher_with_two_formula.send_data(REPORT_3)
        _, msg1 = recv_from_pipe(dummy_pipe_out, 0.5)

        assert msg1 == expected_report_b_report_3
        assert recv_from_pipe(dummy_pipe_out, 0.5) == (None, None)

    @staticmethod
    @define_dispatch_rules([(Report1, DispatchRule1AB(primary=True))])
    def test_send_PoisonPillMessage_make_dispatcher_forward_it_to_formula(dispatcher_with_two_formula):
        """
            Check that a PoissonPillMessage stops the DispatcherActor as well as their formulas
        """
        dispatcher_with_two_formula.send_control(PoisonPillMessage('system-test-dispatcher'))

        sleep(10)

        for _, formula in dispatcher_with_two_formula.state.formula_dict.items():
            assert not formula.is_alive()
        assert not dispatcher_with_two_formula.is_alive()


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
        Generate a test with that extract a formula id from an input report with a given dispatch rule and a primary dispatch rules
        test if the extracted formula_ids are the same that given validation report ids
    """
    formula_ids = extract_formula_id(input_report, dispatch_rule, primary_dispatch_rule)
    formula_ids.sort()
    validation_id.sort()
    assert formula_ids == validation_id


def test_extract_formula_id_with_pgb_DispatchRule1A_on_REPORT_1_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, pgb, REPORT_1, [('a',)])
    gen_test_extract_formula_id(pgb, pgb, REPORT_1_B2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1A_gb_DispatchRule2A_on_REPORT_2_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1A_gb_DispatchRule2AC_on_REPORT_2_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1A(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1AB_on_REPORT_1_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, pgb, REPORT_1, [('a', 'b')])
    gen_test_extract_formula_id(pgb, pgb, REPORT_1_B2, [('a', 'b'), ('a', 'b2')])


def test_extract_formula_id_with_pgb_DispatchRule1AB_gb_DispatchRule2A_on_REPORT_2_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2A(), REPORT_2_C2, [('a',)])


def test_extract_formula_id_with_pgb_DispatchRule1AB_gb_DispatchRule2AC_on_REPORT_2_must_return_good_formula_id():
    """
        Check the formula id extraction
    """
    pgb = DispatchRule1AB(primary=True)
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2, [('a',)])
    gen_test_extract_formula_id(pgb, DispatchRule2AC(), REPORT_2_C2, [('a',)])
