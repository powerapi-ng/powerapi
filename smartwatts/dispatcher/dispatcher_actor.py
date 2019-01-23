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

from smartwatts.actor import Actor, BasicState, SocketInterface
from smartwatts.handler import PoisonPillMessageHandler
from smartwatts.report import Report
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.dispatcher import StartHandler
from smartwatts.utils.tree import Tree
from smartwatts.dispatcher import FormulaDispatcherReportHandler


class NoPrimaryGroupByRuleException(Exception):
    """
    Exception raised when user want to get the primary group_by rule on a
    formula dispatcher that doesn't have one
    """


class PrimaryGroupByRuleAlreadyDefinedException(Exception):
    """
    Exception raised when user want to add a primary group_by rule on a
    formula dispatcher that already have one
    """


class DispatcherState(BasicState):
    """
    DispatcherState class herited from BasicState.

    State that encapsulate formula's dicionary and tree

    :attr:`formula_dict
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_dict>`
    :attr:`formula_tree
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_tree>`
    :attr:`formula_factory
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_factory>`
    """
    def __init__(self, initial_behaviour, socket_interface, formula_factory):
        """
        :param func initial_behaviour: Function that define
                                       the initial_behaviour

        :param socket_interface: Communication interface of the actor
        :type socket_interface: smartwatts.SocketInterface

        :param formula_factory: Factory for Formula creation.
        :type formula_factory: func((formula_id) -> smartwatts.Formula)
        """
        BasicState.__init__(self, initial_behaviour, socket_interface)

        #: (dict): Store the formula by id
        self.formula_dict = {}

        #: (utils.Tree): Tree store of the formula for faster
        #: GroupBy
        self.formula_tree = Tree()

        #: (func): Factory for formula creation
        self.formula_factory = formula_factory

    def add_formula(self, formula_id):
        """
        Create a formula corresponding to the given formula id
        and add it in memory

        :param tuple formula_id: Define the key corresponding to
                                 a specific Formula
        """

        formula = self.formula_factory(formula_id,
                                       self.socket_interface.context)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)
        self.formula_dict[formula_id].start()

    def get_direct_formula(self, formula_id):
        """
        Get the formula corresponding to the given formula id
        or None if no formula correspond to this id

        :param tuple formula_id: Key corresponding to a Formula
        :return: a Formula
        :rtype: Formula or None
        """
        if formula_id not in self.formula_dict:
            return None
        return self.formula_dict[formula_id]

    def get_corresponding_formula(self, formula_id):
        """
        Get the Formulas which have id match with the given formula_id

        :param tuple formula_id: Key corresponding to a Formula
        :return: All Formulas that match with the key
        :rtype: list(Formula)
        """
        return self.formula_tree.get(formula_id)

    def get_all_formula(self):
        """
        Get all the Formula created by the Dispatcher

        :return: List of the Formula
        :rtype: list((formula_id, Formula), ...)
        """
        return self.formula_dict.items()


class DispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self, name, formula_init_function, verbose=False,
                 timeout=None):
        """
        :param str name: Actor name
        :param func formula_init_function: Function for creating Formula
        :param bool verbose: Allow to display log
        :param bool timeout: Define the time in millisecond to wait for a
                             message before run timeout_handler
        """
        Actor.__init__(self, name, verbose)

        #: (array): Array of tuple that link a Report type to a GroupBy rule
        self.route_table = []

        #: (smartwatts.GroupBy): Allow to define how to create the Formula id
        self.primary_group_by_rule = None

        # (func): Function for creating Formula
        self.formula_init_function = formula_init_function

        # (smartwatts.DispatcherState): Actor state
        self.state = DispatcherState(Actor._initial_behaviour,
                                     SocketInterface(name, timeout),
                                     self._create_factory())

    def setup(self):
        """
        Check if there is a primary group by rule. Set define
        StartMessage, PoisonPillMessage and Report handlers
        """
        Actor.setup(self)
        if self.primary_group_by_rule is None:
            raise NoPrimaryGroupByRuleException()

        handler = FormulaDispatcherReportHandler(self.route_table,
                                                 self.primary_group_by_rule)
        self.add_handler(Report, handler)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, StartHandler())

    def terminated_behaviour(self):
        """
        Override from Actor.

        Kill each formula before terminate
        """
        for name, formula in self.state.get_all_formula():
            self.log('kill ' + str(name))
            formula.send_data(PoisonPillMessage())
            formula.join()

    def _create_factory(self):
        """
        Create the full Formula Factory

        :return: Formula Factory
        :rtype: func(formula_id, context) -> Formula
        """
        # context = self.state.socket_interface.context
        formula_init_function = self.formula_init_function
        verbose = self.verbose

        def factory(formula_id, context):
            formula = formula_init_function(str(formula_id), verbose)
            formula.connect_data(context)
            formula.connect_control(context)
            return formula

        return factory

    def group_by(self, report_class, group_by_rule):
        """
        Add a group_by rule to the formula dispatcher

        :param Type report_class: Type of the message that the
                                  group_by rule must handle
        :param group_by_rule: Group_by rule to add
        :type group_by_rule:  smartwatts.group_by.GroupBy
        """
        if group_by_rule.is_primary:
            if self.primary_group_by_rule is not None:
                raise PrimaryGroupByRuleAlreadyDefinedException()
            self.primary_group_by_rule = group_by_rule

        self.route_table.append((report_class, group_by_rule))
