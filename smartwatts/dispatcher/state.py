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

from smartwatts.actor import State
from smartwatts.utils.tree import Tree
from smartwatts.message import UnknowMessageTypeException

class PrimaryGroupByRuleAlreadyDefinedException(Exception):
    """
    Exception raised when user want to add a primary group_by rule on a
    formula dispatcher that already have one
    """


class RouteTable:
    """
    Structure that map a :class:`Report<smartwatts.report.Report>` type to a
    :class:`GroupBy<smartwatts.group_by.GroupBy>` rule
    """

    def __init__(self):
        #: (array): Array of tuple that link a Report type to a GroupBy rule
        self.route_table = []
        #: (smartwatts.GroupBy): Allow to define how to create the Formula id
        self.primary_group_by_rule = None

    def get_group_by_rule(self, msg):
        """
        Return the corresponding group by rule mapped to the received message
        type

        :param type msg: the received message
        :return: the group_by rule mapped to the received message type
        :rtype: smartwatts.group_by.GroupBy
        :raise: UnknowMessageTypeException if no group by rule is mapped to the
                received message type
        """
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                return group_by_rule

        raise UnknowMessageTypeException(type(msg))

    def group_by(self, report_class, group_by_rule):
        """
        Add a group_by rule to the route table

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


class DispatcherState(State):
    """
    DispatcherState class herited from State.

    State that encapsulate formula's dicionary and tree

    :attr:`formula_dict
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_dict>`
    :attr:`formula_tree
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_tree>`
    :attr:`formula_factory
    <smartwatts.dispatcher.dispatcher_actor.DispatcherState.formula_factory>`
    """
    def __init__(self, initial_behaviour, socket_interface, formula_factory,
                 route_table):
        """
        :param func initial_behaviour: Function that define
                                       the initial_behaviour

        :param socket_interface: Communication interface of the actor
        :type socket_interface: smartwatts.SocketInterface

        :param formula_factory: Factory for Formula creation.
        :type formula_factory: func((formula_id) -> smartwatts.Formula)
        :param route_table: initialized route table
        :type route_table: smartwatts.dispatcher.state.RouteTable
        """
        State.__init__(self, initial_behaviour, socket_interface)

        #: (dict): Store the formula by id
        self.formula_dict = {}

        #: (utils.Tree): Tree store of the formula for faster
        #: GroupBy
        self.formula_tree = Tree()

        #: (func): Factory for formula creation
        self.formula_factory = formula_factory

        self.route_table = route_table

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
        or create and return it if its didn't exist

        :param tuple formula_id: Key corresponding to a Formula
        :return: a Formula
        :rtype: Formula or None
        """
        if formula_id not in self.formula_dict:
            self.add_formula(formula_id)
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
