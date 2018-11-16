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

from smartwatts.actor import Actor, Handler
from smartwatts.report import Report
from smartwatts.message import UnknowMessageTypeException
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


class FormulaDispatcherReportHandler(Handler):
    """
    Split the received report into sub-reports (if needed) and return the sub
    reports and formulas ids to send theses report
    """

    def __init__(self, route_table, primary_group_by_rule):
        """
        Parameters:
            @formula_init_function(fun () -> smartwatts.formula.Formula):
                Formula Factory.
        """
        # Array of tuple (report_class, group_by_rule)
        self.route_table = route_table

        # Primary GroupBy
        self.primary_group_by_rule = primary_group_by_rule

    def handle(self, msg):
        """
        Split the received report into sub-reports (if needed) and return the
        sub reports and formulas ids to send theses report

        Parameters:
            msg(smartwatts.report.Report)

        Return:
            [(tuple, smartwatts.report.Report)]: list of *(formula_id, report)*.
                                                 The formula_id is a tuple that
                                                 identify the formula_actor
        """
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                return self._extract_reports(msg, group_by_rule)

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
        primary_rule = self._get_primary_group_by_rule()
        for i in range(len(report_id)):
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

        # Formula containers
        self.formula_dict = {}
        self.formula_tree = Tree()

        # Formula factory
        self.formula_init_function = formula_init_function

    def setup(self):
        """ Append FormulaDispatcherReportHandler Handler"""
        if self.primary_group_by_rule is None:
            raise NoPrimaryGroupByRuleException

        self.handlers.append(
            (Report, FormulaDispatcherReportHandler(self.route_table,
                                                    self.primary_group_by_rule))
        )

    def _post_handle(self, result):
        """ Send the report to each formulas """
        for formula_id, report in result:
            self._send_to_formula(report, formula_id)

    def terminated_behaviour(self):
        """
        Kill each formula before terminate
        """
        for name, formula in self.formula_dict.items():
            self.log('kill ' + name)
            formula.kill()

    def _send_to_formula(self, report, formula_id):
        """
        Send the report to all the formula that match the formula_id

        if the formula id identify an unique formula and the formula doesn't
        exist, create it
        """
        if len(formula_id) == len(self.primary_group_by_rule.fields):
            if formula_id not in self.formula_dict:
                self._create_formula(formula_id)
            self.formula_dict[formula_id].send(report)
        else:
            for formula in self.formula_tree.get(list(formula_id)):
                formula.send(report)

    def _create_formula(self, formula_id):
        """
        Create formula from router
        """
        formula = self.formula_init_function(str(formula_id), self.verbose)

        formula.connect(self.context)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)
        self.formula_dict[formula_id].start()
        self.log('create formula ' + str(formula_id))

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
                raise PrimaryGroupByRuleAlreadyDefinedException
            self.primary_group_by_rule = group_by_rule

        self.route_table.append((report_class, group_by_rule))
