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

from powerapi.handler import InitHandler, Handler, StartHandler
from powerapi.message import OKMessage, StartMessage


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


class FormulaDispatcherReportHandler(InitHandler):
    """
    Split received report into sub-reports (if needed) and return the sub
    reports and formulas ids to send theses reports.
    """

    def handle(self, msg, state):
        """
        Split the received report into sub-reports (if needed) and send them to
        their corresponding formula.

        If the corresponding formula does not exist, create and return the
        actor state, containing the new formula.

        :param powerapi.Report msg:       Report message
        :param powerapi.State state: Actor state

        :return: List of the (formula_id, report) where formula_id is a tuple
                 that identitfy the formula_actor
        :rtype:  list(tuple(formula_id, report))
        """
        dispatch_rule = state.route_table.get_dispatch_rule(msg)
        primary_dispatch_rule = state.route_table.primary_dispatch_rule

        for formula_id in self._extract_formula_id(msg, dispatch_rule,
                                                   primary_dispatch_rule):
            primary_rule_fields = primary_dispatch_rule.fields
            if len(formula_id) == len(primary_rule_fields):
                formula = state.get_direct_formula(formula_id)
                formula.send_data(msg)

            else:
                for formula in state.get_corresponding_formula(
                        list(formula_id)):
                    formula.send(msg)

        return state


    def _extract_formula_id(self, report, dispatch_rule, primary_dispatch_rule):
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

        return _clean_list(list(map(
            lambda id: (self._match_report_id(id, dispatch_rule,
                                              primary_dispatch_rule)),
            id_list)))



    def _match_report_id(self, report_id, dispatch_rule, primary_rule):
        """
        Return the new_report_id with the report_id by removing
        every "useless" fields from it.

        :param tuple report_id:                          Original report id
        :param powerapi.DispatchRule dispatch_rule: DispatchRule rule
        """
        new_report_id = ()
        for i in range(len(report_id)):
            if i >= len(primary_rule.fields):
                return new_report_id
            if dispatch_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id
