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

import logging

import pytest

from powerapi.actor import NotConnectedException, ActorInitError, Supervisor
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.message import StartMessage, OKMessage, ErrorMessage, UnknowMessageTypeException
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel, DispatchRule
from powerapi.report import *
from tests.utils import *
from tests.integration.dispatcher.fake_formula import FakeFormulaActor
from powerapi.dispatcher import NoPrimaryDispatchRuleRuleException


FORMULA_SOCKET_ADDR = 'ipc://@test_formula_socket'
LOG_LEVEL = logging.NOTSET


####################
# Fixtures utility #
####################
def define_route_table(route_table):
    """
    A decorator to set the _route_table
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_route_table', route_table)
        return func
    return wrap


def define_formula_init_msg(formula_init_msg):
    """
    A decorator to set the _formula_init_msg
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_formula_init_msg', formula_init_msg)
        return func
    return wrap


def receive(socket):
    """
    wait for a message reception on a given socket and return it
    return None if no message was receive until 500ms
    """
    event = socket.poll(500)
    if event == 0:
        return None
    return pickle.loads(socket.recv())


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    define the route_table fixtures in test environement with collected the
    value _route_table if it exist or with an empty RouteTable

    :param metafunc: the test context given by pytest
    """
    if 'route_table' in metafunc.fixturenames:
        route_table = getattr(metafunc.function, '_route_table', None)
        if isinstance(route_table, RouteTable):
            metafunc.parametrize('route_table', [route_table])
        elif route_table == 'all':
            metafunc.parametrize('route_table',
                                 [route_table_no_hwpc(),
                                  route_table_hwpc_not_primary(),
                                  route_table_with_primary_rule()])
        else:
            metafunc.parametrize('route_table', [RouteTable()])

    if 'formula_init_msg' in metafunc.fixturenames:
        formula_init_msg = getattr(metafunc.function, '_formula_init_msg', None)
        if isinstance(formula_init_msg, Report):
            metafunc.parametrize('formula_init_msg', [[formula_init_msg]])
        elif formula_init_msg == 'all':
            metafunc.parametrize('formula_init_msg',
                                 [[], [gen_good_report()]])
        else:
            metafunc.parametrize('formula_init_msg', [[]])


##############
#  Fixtures  #
##############
@pytest.fixture()
def dispatcher(request, route_table):
    """
    return an instance of a DispatcherActor that is not launched
    """
    dispatcher_actor = DispatcherActor(
        'test_dispatcher-',
        lambda name, log: FakeFormulaActor(name, FORMULA_SOCKET_ADDR,
                                           level_logger=log),
        route_table,
        level_logger=LOG_LEVEL)
    return dispatcher_actor


@pytest.fixture()
def initialized_dispatcher(dispatcher):
    """

    Return a DispatcherActor, start it, connect its sockets and send it a
    StartMessage

    teardown : terminate the Dispatcher process and close open sockets
    """
    supervisor = Supervisor()
    supervisor.launch_actor(dispatcher)
    yield dispatcher
    dispatcher.socket_interface.close()
    dispatcher.terminate()
    dispatcher.join()


@pytest.fixture()
def dispatcher2(request, route_table):
    """
    return an instance of a second DispatcherActor with the same name that the
    first dispatcher that is not launched the teardown of this fixtures
    terminate the actor (in case it was started and close its socket)
    """
    dispatcher_actor = DispatcherActor(
        'test_dispatcher-',
        lambda name, log: FakeFormulaActor(name, FORMULA_SOCKET_ADDR,
                                           level_logger=log),
        route_table,
        level_logger=LOG_LEVEL)
    yield dispatcher_actor
    dispatcher_actor.socket_interface.close()
    dispatcher_actor.terminate()
    dispatcher_actor.join()


@pytest.fixture()
def dispatcher3(request, route_table):
    """
    return an instance of a second DispatcherActor with another name that is
    not launched the teardown of this fixtures terminate the actor (in case it
    was started and close its socket)
    """
    dispatcher_actor = DispatcherActor(
        'test_dispatcher2-',
        lambda name, log: FakeFormulaActor(name, FORMULA_SOCKET_ADDR,
                                           level_logger=log),
        route_table,
        level_logger=LOG_LEVEL)
    yield dispatcher_actor
    dispatcher_actor.socket_interface.close()
    dispatcher_actor.terminate()
    dispatcher_actor.join()


@pytest.fixture()
def bad_report():
    """
    Return a badly formated HWPCReport
    """
    return create_report_root([])


@pytest.fixture()
def formula_socket():
    """
    return the socket that will be used by the FakeFormula actors to log their
    actions
    """
    socket = zmq.Context.instance().socket(zmq.PULL)
    socket.bind(FORMULA_SOCKET_ADDR)
    yield socket
    socket.close()


@pytest.fixture()
def dispatcher_with_formula(formula_init_msg, initialized_dispatcher,
                            route_table, formula_socket):
    """
    return a dispatcher with formula
    """
    for msg in formula_init_msg:
        try:
            gb_rule = route_table.get_dispatch_rule(msg)
            if not gb_rule.is_primary:
                msg = FakeReport()
            initialized_dispatcher.send_data(msg)
        except UnknowMessageTypeException:
            msg = FakeReport()
            initialized_dispatcher.send_data(msg)
        assert receive(formula_socket) == 'created'
        assert receive(formula_socket) == msg

    yield initialized_dispatcher
    # wait for formula termination
    for msg in formula_init_msg:
        receive(formula_socket)


###################
# Report Creation #
###################
def gen_good_report():
    """
    Return a well formated HWPCReport
    """
    cpua = create_core_report('1', 'e0', '0')
    cpub = create_core_report('2', 'e0', '1')
    cpuc = create_core_report('1', 'e0', '2')
    cpud = create_core_report('2', 'e0', '3')
    cpue = create_core_report('1', 'e1', '0')
    cpuf = create_core_report('2', 'e1', '1')
    cpug = create_core_report('1', 'e1', '2')
    cpuh = create_core_report('2', 'e1', '3')

    socketa = create_socket_report('1', [cpua, cpub])
    socketb = create_socket_report('2', [cpuc, cpud])
    socketc = create_socket_report('1', [cpue, cpuf])
    socketd = create_socket_report('2', [cpug, cpuh])

    groupa = create_group_report('1', [socketa, socketb])
    groupb = create_group_report('2', [socketc, socketd])

    return create_report_root([groupa, groupb])


#################################
# Route Table creation function #
#################################
class FakeReport(Report):
    """
    Empty report
    """
    def __init__(self):
        Report.__init__(self, timestamp=datetime.fromtimestamp(0),
                        sensor='toto', target='system')

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                self.timestamp == other.timestamp and
                self.sensor == other.sensor and self.target == other.target)


class FakeGBR(DispatchRule):
    """
    DispatchRule Rule that can handle FakeReport type
    """
    def __init__(self, primary=False):
        self.is_primary = primary
        self.fields = ['sensor']

    def get_formula_id(self, report):
        """
        return the report and the sensor name as identifier
        """
        return [('toto',)]

    def __str__(self):
        return 'MESSAGE OTHER GBR'


def route_table_no_hwpc():
    """
    return a RouteTable with :
      - a FakeGBR as primary rule
    """
    route_table = RouteTable()
    route_table.dispatch_rule(FakeReport, FakeGBR(primary=True))
    return route_table


def empty_route_table():
    """
    return a RouteTable with no rule
    """
    return RouteTable()


def route_table_hwpc_not_primary():
    """
    return a RouteTable with :
      - a FakeGBR as primary rule
      - a HWPCGrouptBy rule
    """
    route_table = RouteTable()
    route_table.dispatch_rule(FakeReport, FakeGBR(primary=True))
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(HWPCDepthLevel.ROOT))

    return route_table


def route_table_with_primary_rule():
    """
    return a RouteTable with :
      - a HWPCGrouptBy rule as primary rule
    """
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(HWPCDepthLevel.ROOT,
                                                           primary=True))
    return route_table


##################
# Actor creation #
##################
@define_route_table(empty_route_table())
def test_create_dispatcher_without_primary(dispatcher2):
    """
    Create a Dispatcher with no primary dispatch rule

    Test if the actor actor initialisation raise an ActorInitError
    """
    with pytest.raises(ActorInitError):
        Supervisor().launch_actor(dispatcher2)


@define_route_table(route_table_with_primary_rule())
def test_create_dispatcher_with_primary(initialized_dispatcher):
    """
    Create a Dispatcher with a PrimaryDispatchRule rule

    Test if the actor is alive after its initialisation

    """
    assert is_actor_alive(initialized_dispatcher)


##################
# Initialisation #
##################
@define_route_table(route_table_with_primary_rule())
def test_send_StartMessage_dispatcher_already_init(initialized_dispatcher):
    """
    Create a Dispatcher with a PrimaryDispatchRule rule, initialize it and send
    it another StartMessage

    Test :
      - if the actor is alive
      - if the actor sent a ErrorMessage on the control canal

    """
    initialized_dispatcher.send_control(StartMessage())
    assert is_actor_alive(initialized_dispatcher)
    assert isinstance(initialized_dispatcher.receive_control(), ErrorMessage)


@define_route_table(route_table_with_primary_rule())
def test_init_dispatcher(initialized_dispatcher):
    """
    Create a Dispatcher with a PrimaryDispatchRule rule and send it a
    StartMessage

    Test :
      - if the actor is alive
    """
    assert is_actor_alive(initialized_dispatcher)


####################
# Multi-Dispatcher #
####################
@define_route_table(route_table_with_primary_rule())
def test_create_double_dispatcher(initialized_dispatcher, dispatcher3):
    """
    Create two dispatcher with different names
    Test :
      - if the two dispatcher are alive
    """
    Supervisor().launch_actor(dispatcher3)
    assert is_actor_alive(dispatcher3)
    assert is_actor_alive(initialized_dispatcher)


@define_route_table(route_table_with_primary_rule())
def test_create_formula_double_dispatcher(initialized_dispatcher, dispatcher3, formula_socket):
    """
    Create two dispatcher with different names but same dispatch rules and send
    them the same HWPCReport

    Test:
      - if each dispatcher are alive
      - if each dispatcher create one formula
    """
    Supervisor().launch_actor(dispatcher3)
    initialized_dispatcher.send_data(gen_good_report())
    assert is_actor_alive(initialized_dispatcher)
    assert receive(formula_socket) == 'created'
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None

    dispatcher3.send_data(gen_good_report())
    assert is_actor_alive(dispatcher3)
    assert receive(formula_socket) == 'created'
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None


##########
#  Kill  #
##########
@define_route_table(route_table_with_primary_rule())
def test_kill_non_init_dispatcher(dispatcher):
    """
    Create a Dispatcher and call its kill method

    Test :
      - if the actor is terminated
    """
    with pytest.raises(NotConnectedException):
        dispatcher.send_kill()


@define_route_table(route_table_with_primary_rule())
def test_kill_init_dispatcher(initialized_dispatcher):
    """
    Create an initialized Dispatcher and call its kill method

    Test :
      - if the actor is terminated
    """
    initialized_dispatcher.send_kill()
    assert not is_actor_alive(initialized_dispatcher)


@define_route_table(route_table_with_primary_rule())
@define_formula_init_msg(gen_good_report())
def test_kill_dispatcher_with_formula(dispatcher_with_formula, formula_socket):
    """
    Create an initialized Dispatcher with one formula and then kill it

    Test :
      - if the actor is terminated
      - if the created formula was terminated
    """
    dispatcher_with_formula.send_kill()
    assert not is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) == 'terminated'


######################
# Receive HWPCReport #
######################
#@define_route_table('all')
#@define_formula_init_msg('all')
#def test_bad_report_receive(bad_report, dispatcher_with_formula,
#                            formula_socket):
#    """
#    test to send a badly formated HWPCReport to an initialized Dispatcher
#
#    Dispatcher will be tested with different route table :
#      - a route table with no rule for HWPCReport
#      - a route table with a normal rule for HWPCReport
#      - a route table with a primary rule for HWPCReport
#
#    for each route table, the dispatcher will have no formula initialized or
#    already a formula to handle this report
#
#    For each case, test :
#      - if the process is alive
#      - if the already created formula are alive
#      - if no more formula was created
#      - if the already created formula didn't receive any message from the
#        dispatcher
#    """
#    dispatcher_with_formula.send_data(bad_report)
#    assert is_actor_alive(dispatcher_with_formula)
#    assert receive(formula_socket) is None


@define_formula_init_msg('all')
@define_route_table(route_table_no_hwpc())
def test_good_report_no_rule(formula_init_msg,dispatcher_with_formula,
                             formula_socket):
    """
    send a well formated HWPCReport to an initialized Dispatcher with no rule
    for HWPCReport

    the dispatcher will have no formula initialized or already a formula to
    handle this report

    For each case, test :
      - if the process is alive
      - if the already created formula are alive
      - if no more formula was created
      - if the already created formula didn't receive any message from the
        dispatcher
    """
    dispatcher_with_formula.send_data(gen_good_report())
    assert is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) is None


@define_route_table(route_table_hwpc_not_primary())
@define_formula_init_msg(FakeReport())
def test_good_report_normal_rule_formula_ok(dispatcher_with_formula,
                                            formula_socket, route_table):
    """
    send a well formated HWPCReport to an initialized Dispatcher with a
    normal rule for HWPCReport and a formula to handle this report

    Test :
      - if the process is alive
      - if the already created formula are alive
      - if no more formula was created
      - if the already created formula receive the report
    """
    dispatcher_with_formula.send_data(gen_good_report())
    assert is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None


@define_route_table(route_table_hwpc_not_primary())
def test_good_report_normal_rule_no_formula(dispatcher_with_formula,
                                            formula_socket, route_table):
    """
    send a well formated HWPCReport to an initialized Dispatcher with a
    normal rule for HWPCReport and no formula to handle this report

    Test :
      - if the process is alive
      - if a formula was created
      - if the created formula receive the report
    """
    dispatcher_with_formula.send_data(gen_good_report())
    assert is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) == 'created'
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None


@define_route_table(route_table_with_primary_rule())
@define_formula_init_msg(gen_good_report())
def test_good_report_primary_rule_formula_ok(dispatcher_with_formula,
                                             formula_socket, route_table):
    """
    send a well formated HWPCReport to an initialized Dispatcher with a
    primary rule for HWPCReport and a formula to handle this report

    Test :
      - if the process is alive
      - if the already created formula are alive
      - if no more formula was created
      - if the already created formula receive the report
    """
    dispatcher_with_formula.send_data(gen_good_report())
    assert is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None


@define_route_table(route_table_with_primary_rule())
def test_good_report_primary_rule_no_formula(dispatcher_with_formula,
                                             formula_socket, route_table):
    """
    send a well formated HWPCReport to an initialized Dispatcher with a
    primary rule for HWPCReport and no formula to handle this report

    Test :
      - if the process is alive
      - if a formula was created
      - if the created formula receive the report
    """
    dispatcher_with_formula.send_data(gen_good_report())
    assert is_actor_alive(dispatcher_with_formula)
    assert receive(formula_socket) == 'created'
    assert receive(formula_socket) == gen_good_report()
    assert receive(formula_socket) is None
