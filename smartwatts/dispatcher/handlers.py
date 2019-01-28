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

from smartwatts.handler import InitHandler, Handler
from smartwatts.message import OKMessage, StartMessage


class StartHandler(Handler):
    """
    Initialize the received state
    """

    def handle(self, msg, state):
        """
        Allow to initialize the state of the actor, then reply to the control
        socket.

        :param smartwatts.StartMessage msg: Message that initialize the actor
        :param smartwatts.State state: State of the actor
        """
        if state.initialized:
            return state

        if not isinstance(msg, StartMessage):
            return state

        state.initialized = True
        state.socket_interface.send_control(OKMessage())

        return state


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

        :param smartwatts.Report msg:       Report message
        :param smartwatts.State state: Actor state

        :return: List of the (formula_id, report) where formula_id is a tuple
                 that identitfy the formula_actor
        :rtype:  list(tuple(formula_id, report))
        """
        group_by_rule = state.route_table.get_group_by_rule(msg)
        primary_group_by_rule = state.route_table.primary_group_by_rule

        for formula_id, report in self._extract_reports(msg, group_by_rule,
                                                        primary_group_by_rule):
            primary_rule_fields = primary_group_by_rule.fields
            if len(formula_id) == len(primary_rule_fields):
                formula = state.get_direct_formula(formula_id)
                formula.send_data(report)

            else:
                for formula in state.get_corresponding_formula(
                        list(formula_id)):
                    formula.send(report)

        return state


    def _extract_reports(self, report, group_by_rule, primary_group_by_rule):
        """
        Use the group by rule to split the report. Generated report identifier
        are then mapped to an identifier that match the primary report
        identifier fields

        ex: primary group_by (sensor, socket, core)
            second  group_by (sensor)
        The second group_by need to match with the primary if sensor are equal.

        :param smartwatts.Report report:                 Report to split
        :param smartwatts.GroupBy group_by_rule: GroupBy rule

        :return: List of formula_id associated to a sub-report of report
        :rtype:  list(tuple(formula_id, smartwatts.Report))
        """

        # List of tuple (id_report, report)
        report_list = group_by_rule.extract(report)

        if group_by_rule.is_primary:
            return report_list

        return list(map(lambda _tuple:
                        (self._match_report_id(_tuple[0], group_by_rule,
                                               primary_group_by_rule),
                         _tuple[1]),
                        report_list))

    def _match_report_id(self, report_id, group_by_rule, primary_rule):
        """
        Return the new_report_id with the report_id by removing
        every "useless" fields from it.

        :param tuple report_id:                          Original report id
        :param smartwatts.GroupBy group_by_rule: GroupBy rule
        """
        new_report_id = ()
        for i in range(len(report_id)):
            if i >= len(primary_rule.fields):
                return new_report_id
            if group_by_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id
