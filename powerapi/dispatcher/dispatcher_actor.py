# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
import logging
from typing import Type, Callable, Tuple, Dict, List

from thespian.actors import ActorAddress, ActorExitRequest

from powerapi.actor import Actor, InitializationException
from powerapi.formula import FormulaActor
from powerapi.dispatcher import RouteTable
from powerapi.dispatch_rule import DispatchRule
from powerapi.utils import Tree
from powerapi.report import Report
from powerapi.message import StartMessage


def _clean_list(id_list):
    """
    return a list where all elements are unique
    """
    id_list.sort()
    r_list = []
    last_element = None
    for x in id_list:
        if x != last_element:
            r_list.append(x)
            last_element = x
    return r_list



def _extract_formula_id(report: Report, dispatch_rule: DispatchRule, primary_dispatch_rule: DispatchRule) -> List[Tuple]:
    """
    Use the dispatch rule to extract formula_id from the given report.
    Formula id are then mapped to an identifier that match the primary
    report identifier fields

    ex: primary dispatch_rule (sensor, socket, core)
        second  dispatch_rule (sensor)
    The second dispatch_rule need to match with the primary if sensor are
    equal.

    :param powerapi.Report report:                 Report to split
    :param powerapi.DispatchRule dispatch_rule: DispatchRule rule

    :return: List of formula_id associated to a sub-report of report
    :rtype: [tuple]
    """

    # List of tuple (id_report, report)
    id_list = dispatch_rule.get_formula_id(report)
    if dispatch_rule.is_primary:
        return id_list

    def f(id):
        return _match_report_id(id, dispatch_rule, primary_dispatch_rule)
    
    return _clean_list(list(map(f, id_list)))

def _match_report_id(report_id: Tuple, dispatch_rule: DispatchRule, primary_rule: DispatchRule) -> Tuple:
    """
    Return the new_report_id with the report_id by removing
    every "useless" fields from it.

    :param tuple report_id:                     Original report id
    :param powerapi.DispatchRule dispatch_rule: DispatchRule rule
    """
    print(report_id)
    new_report_id = ()
    for i in range(len(report_id)):
        if i >= len(primary_rule.fields):
            return new_report_id
        if dispatch_rule.fields[i] == primary_rule.fields[i]:
            new_report_id += (report_id[i], )
        else:
            return new_report_id
    return new_report_id


class DispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self):
        """
        :param str name: Actor name
        :param func formula_init_function: Function for creating Formula
        :param route_table: initialized route table of the DispatcherActor
        :type route_table: powerapi.dispatcher.state.RouteTable
        :param int level_logger: Define the level of the logger
        :param bool timeout: Define the time in millisecond to wait for a
                             message before run timeout_handler
        """
        Actor.__init__(self)

        self.name: str = None
        self.formula_class: Type[FormulaActor] = None
        self.formula_config_factory: Callable[[str], Tuple[Type[FormulaActor], Dict]] = None
        self.route_table: RouteTable = None
        self.formula_pool = None

    def _initialization(self, message: StartMessage):
        self.name = message.init_values['name']
        self.formula_class = message.init_values['formula_class']
        self.formula_config_factory = message.init_values['formula_config_factory']
        self.route_table = message.init_values['route_table']
        self.formula_pool = FormulaPool()

        if self.route_table.primary_dispatch_rule is None:
            raise InitializationException('Dispatcher initialized without primary dispatch rule')

    def receiveMsg_ActorExitRequest(self, message: ActorExitRequest, sender: ActorAddress):
        """
        When receiving ActorExitRequest, forward it to all formula
        """
        for formula in self.formula_pool.get_all_formula():
            self.send(formula, ActorExitRequest())

    def receiveMsg_Report(self, message: Report, sender: ActorAddress):
        """
        When receiving a report, split it into sub-reports (if needed) and send them to their corresponding formula.
        If the corresponding formula does not exist, the dispatcher create it and send it the report
        """
        dispatch_rule = self.route_table.get_dispatch_rule(message)
        primary_dispatch_rule = self.route_table.primary_dispatch_rule

        if dispatch_rule is None:
            # todo : logger que le report n'a pas été reconnue par une dispatch rule
            return

        for formula_id in _extract_formula_id(message, dispatch_rule, primary_dispatch_rule):
            primary_rule_fields = primary_dispatch_rule.fields
            if len(formula_id) == len(primary_rule_fields):
                try:
                    formula = self.formula_pool.get_direct_formula(formula_id)
                except KeyError:
                    formula = self._create_formula(formula_id)
                    self.formula_pool.add_formula(formula_id, formula)
                finally:
                    self.send(formula, message)
            else:
                for formula in self.formula_pool.get_corresponding_formula(list(formula_id)):
                    self.send(formula, message)

    def _create_formula(self, formula_id: Tuple):
        formula = self.createActor(self.formula_class)
        config = self.formula_config_factory(str((self.name,) + formula_id))
        self.send(formula, StartMessage(config))
        return formula


class FormulaPool:
    def __init__(self):
        self.formula_dict = {}
        self.formula_tree = Tree()

    def add_formula(self, formula_id, formula):
        """
        Create a formula corresponding to the given formula id
        and add it in memory

        :param tuple formula_id: Define the key corresponding to
                                 a specific Formula
        """
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
