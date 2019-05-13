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

from powerapi.actor import State
from powerapi.utils.tree import Tree
from powerapi.message import UnknowMessageTypeException


class PrimaryDispatchRuleRuleAlreadyDefinedException(Exception):
    """
    Exception raised when user want to add a primary dispatch_rule rule on a
    formula dispatcher that already have one
    """


class RouteTable:
    """
    Structure that map a :class:`Report<powerapi.report.Report>` type to a
    :class:`DispatchRule<powerapi.dispatch_rule.DispatchRule>` rule
    """

    def __init__(self):
        #: (array): Array of tuple that link a Report type to a DispatchRule
        # rule
        self.route_table = []
        #: (powerapi.DispatchRule): Allow to define how to create the Formula id
        self.primary_dispatch_rule = None

    def get_dispatch_rule(self, msg):
        """
        Return the corresponding group by rule mapped to the received message
        type

        :param type msg: the received message
        :return: the dispatch_rule rule mapped to the received message type
        :rtype: powerapi.dispatch_rule.DispatchRule
        :raise: UnknowMessageTypeException if no group by rule is mapped to the
                received message type
        """
        for (report_class, dispatch_rule) in self.route_table:
            if isinstance(msg, report_class):
                return dispatch_rule

        raise UnknowMessageTypeException(type(msg))

    def dispatch_rule(self, report_class, dispatch_rule):
        """
        Add a dispatch_rule rule to the route table

        :param Type report_class: Type of the message that the
                                  dispatch_rule rule must handle
        :param dispatch_rule: Group_by rule to add
        :type dispatch_rule:  powerapi.dispatch_rule.DispatchRule
        """
        if dispatch_rule.is_primary:
            if self.primary_dispatch_rule is not None:
                raise PrimaryDispatchRuleRuleAlreadyDefinedException()
            self.primary_dispatch_rule = dispatch_rule

        self.route_table.append((report_class, dispatch_rule))


class DispatcherState(State):
    """
    DispatcherState class herited from State.

    State that encapsulate formula's dicionary and tree

    :attr:`formula_dict
    <powerapi.dispatcher.dispatcher_actor.DispatcherState.formula_dict>`
    :attr:`formula_tree
    <powerapi.dispatcher.dispatcher_actor.DispatcherState.formula_tree>`
    :attr:`formula_factory
    <powerapi.dispatcher.dispatcher_actor.DispatcherState.formula_factory>`
    """
    def __init__(self, actor, formula_factory, route_table):
        """
        :param func initial_behaviour: Function that define
                                       the initial_behaviour

        :param socket_interface: Communication interface of the actor
        :type socket_interface: powerapi.SocketInterface

        :param formula_factory: Factory for Formula creation.
        :type formula_factory: func((formula_id) -> powerapi.Formula)
        :param route_table: initialized route table
        :type route_table: powerapi.dispatcher.state.RouteTable
        """
        State.__init__(self, actor)

        #: (dict): Store the formula by id
        self.formula_dict = {}

        #: (utils.Tree): Tree store of the formula for faster
        #: DispatchRule
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

        formula = self.formula_factory(formula_id)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)

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
