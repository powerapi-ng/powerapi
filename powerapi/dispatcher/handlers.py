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
    
    def handle(self, msg):
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
        dispatch_rule = self.state.route_table.get_dispatch_rule(msg)
        primary_dispatch_rule = self.state.route_table.primary_dispatch_rule

        for formula_id in self._extract_formula_id(msg, dispatch_rule,
                                                   primary_dispatch_rule):
            primary_rule_fields = primary_dispatch_rule.fields
            if len(formula_id) == len(primary_rule_fields):
                formula = self.state.get_direct_formula(formula_id)
                formula.send_data(msg)

            else:
                for formula in self.state.get_corresponding_formula(
                        list(formula_id)):
                    formula.send(msg)

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
