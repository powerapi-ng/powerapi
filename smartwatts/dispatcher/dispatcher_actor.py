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

from smartwatts.actor import Actor, BasicState
from smartwatts.handler import AbstractHandler, PoisonPillMessageHandler
from smartwatts.report import Report
from smartwatts.message import PoisonPillMessage, UnknowMessageTypeException
from smartwatts.utils.tree import Tree


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
    def __init__(self, initial_behaviour, formula_factory):

        BasicState.__init__(self, initial_behaviour)
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


class FormulaDispatcherReportHandler(AbstractHandler):
    """
    Split the received report into sub-reports (if needed) and return the sub
    reports and formulas ids to send theses report
    """

    def __init__(self, route_table, primary_group_by_rule):
        """
        Parameters:
            @route_table([(Message, AbstractGroupBy)]: list all group by rule
                                                       with their associated
                                                       message type

        """
        # Array of tuple (report_class, group_by_rule)
        self.route_table = route_table

        # Primary GroupBy
        self.primary_group_by_rule = primary_group_by_rule

    def handle(self, msg, state):
        """
        Split the received report into sub-reports (if needed) and send them to
        their corresponding formula

        if the corresponfing formula does not exist, create and return the
        actor state, containing the new formula

        Parameters:
            msg(smartwatts.report.Report)

        Return:
            [(tuple, smartwatts.report.Report)]: list of *(formula_id, report)*.
                                                 The formula_id is a tuple that
                                                 identify the formula_actor
        """
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                for formula_id, report in self._extract_reports(msg,
                                                                group_by_rule):
                    primary_rule_fields = self.primary_group_by_rule.fields
                    if len(formula_id) == len(primary_rule_fields):
                        formula = state.get_direct_formula(formula_id)
                        if formula is None:
                            state.add_formula(formula_id)
                        else:
                            formula.send(report)
                    else:
                        for formula in state.get_corresponding_formula(
                                list(formula_id)):
                            formula.send(report)

                return state

        raise UnknowMessageTypeException(type(msg))

    def _extract_reports(self, report, group_by_rule):
        """
        Use the group by rule to split the report. Generated report identifier
        are then mapped to an identifier that match the primary report
        identifier fields

        ex: primary group_by (sensor, socket, core)
            second  group_by (sensor)
        The second group_by need to match with the primary if sensor are equal.

        Parameters:
            @report:        XXXReport instance
            @group_by_rule: XXXGroupBy instance

        Return:
            ([(tuple, Report]): list of (formula_id, Report)
        """

        # List of tuple (id_report, report)
        report_list = group_by_rule.extract(report)

        if group_by_rule.is_primary:
            return report_list

        return list(map(lambda _tuple:
                        (self._match_report_id(_tuple[0], group_by_rule),
                         _tuple[1]),
                        report_list))

    def _match_report_id(self, report_id, group_by_rule):
        """
        Return the new_report_id with the report_id by removing
        every "useless" fields from it.

        Parameters:
            @report_id:     tuple of fields (id)
            @group_by_rule: XXXGroupBy instance
        """
        new_report_id = ()
        primary_rule = self.primary_group_by_rule
        for i in range(len(report_id)):
            if i >= len(primary_rule.fields):
                return new_report_id
            if group_by_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id


class DispatcherActor(Actor):
    """
    DispatcherActor class.

    receive interface:
        report_data: route this message to the corresponding Formula Actor,
                     create a new one if no Formula exist to handle
                     this message
    """

    def __init__(self, name, formula_init_function, verbose=False):
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

    def setup(self):
        """ Append FormulaDispatcherReportHandler Handler"""
        if self.primary_group_by_rule is None:
            raise NoPrimaryGroupByRuleException()

        self.state = DispatcherState(self._initial_behaviour,
                                     self._create_factory())

        handler = FormulaDispatcherReportHandler(self.route_table,
                                                 self.primary_group_by_rule)
        self.add_handler(Report, handler)
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())


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
        context = self.context
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
