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

"""
Module class DispatcherActor
"""

from smartwatts.actor import Actor, BasicState, SocketInterface
from smartwatts.handler import PoisonPillMessageHandler
from smartwatts.report import Report
from smartwatts.message import PoisonPillMessage, StartMessage
from smartwatts.dispatcher import StartHandler
from smartwatts.utils.tree import Tree
from smartwatts.dispatcher import FormulaDispatcherReportHandler


class NoPrimaryGroupByRuleException(Exception):
    """
    Exception launched when user want to get the primary group_by rule on a
    formula dispatcher that doesn't have one
    """
    pass


class PrimaryGroupByRuleAlreadyDefinedException(Exception):
    """
    Exception launched when user want to add a primary group_by rule on a
    formula dispatcher that already have one
    """
    pass


class DispatcherState(BasicState):
    """ State tat encapsulate formula's dicionary and tree
    """
    def __init__(self, initial_behaviour, socket_interface, formula_factory):

        BasicState.__init__(self, initial_behaviour, socket_interface)
        """
        Parameters:
            @formula_factory(fun (formula_id) -> smartwatts.formula.Formula):
                    initialize a formula
        """
        # Formula containers
        self.formula_dict = {}
        self.formula_tree = Tree()
        self.formula_factory = formula_factory

    def add_formula(self, formula_id):
        """Create a formula corresponding to the given formula id
        and add it to the state

        """

        formula = self.formula_factory(formula_id)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)
        self.formula_dict[formula_id].start()

    def get_direct_formula(self, formula_id):
        """ Return the formula corresponding to the given formula id
            Return None if no formula correspond to this id
        """
        if formula_id not in self.formula_dict:
            return None
        return self.formula_dict[formula_id]

    def get_corresponding_formula(self, formula_id):
        """ return the formulas wich their id math the given formula id

        Parameter:
            formula_id(list)
        """
        return self.formula_tree.get(formula_id)

    def get_all_formula(self):
        """ return all the formula in the actor state

        Return:
            ([(tuple, Formula)]): list of (formula_id, Formula)

        """
        return self.formula_dict.items()


class DispatcherActor(Actor):
    """
    DispatcherActor class.

    receive interface:
        report_data: route this message to the corresponding Formula Actor,
                     create a new one if no Formula exist to handle
                     this message
    """

    def __init__(self, name, formula_init_function, verbose=False,
                 timeout=None):
        """
        Parameters:
            @formula_init_function(fun () -> smartwatts.formula.Formula):
                Formula Factory.
        """
        Actor.__init__(self, name, verbose)

        # Informations tranmsitted to FormulaDispatcherReportHandler
        self.route_table = []
        self.primary_group_by_rule = None

        # Formula factory
        self.formula_init_function = formula_init_function

        self.state = DispatcherState(Actor._initial_behaviour,
                                     SocketInterface(name, timeout),
                                     self._create_factory())

    def setup(self):
        """ Append FormulaDispatcherReportHandler Handler"""
        if self.primary_group_by_rule is None:
            raise NoPrimaryGroupByRuleException()

        handler = FormulaDispatcherReportHandler(self.route_table,
                                                 self.primary_group_by_rule)
        self.add_handler(Report, handler)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, StartHandler())

    def terminated_behaviour(self):
        """
        Kill each formula before terminate
        """
        for name, formula in self.state.get_all_formula():
            self.log('kill ' + str(name))
            formula.kill()
            formula.join()

    def _create_factory(self):
        """
        Create formula from router
        """
        context = self.state.socket_interface.context
        formula_init_function = self.formula_init_function
        verbose = self.verbose

        def factory(formula_id):
            formula = formula_init_function(str(formula_id), verbose)
            formula.connect(context)

        return factory

    def group_by(self, report_class, group_by_rule):
        """
        Add a group_by rule to the formula dispatcher

        Parameters:
            @report_class(type): type of the message that the
                                 groub_by rule must handle
            @group_by_rule(group_by.AbstractGroupBy): group_by rule to add
        """
        if group_by_rule.is_primary:
            if self.primary_group_by_rule is not None:
                raise PrimaryGroupByRuleAlreadyDefinedException()
            self.primary_group_by_rule = group_by_rule

        self.route_table.append((report_class, group_by_rule))
