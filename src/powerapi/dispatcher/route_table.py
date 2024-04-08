# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

from powerapi.dispatch_rule import DispatchRule
from powerapi.report import Report


class RouteTable:
    """
    Routing Table used by the Dispatcher to map report types to dispatch rules.
    """

    def __init__(self):
        """
        Initializes a new Routing Table.
        """
        self.route_table = {}
        self.primary_dispatch_rule = None

    def get_dispatch_rule(self, report: Report) -> DispatchRule | None:
        """
        Return the corresponding dispatch rule for the given report.
        param msg: The report to get the dispatch rule for
        return: The corresponding dispatch rule or None if no dispatch rule exists for the report type.
        """
        return self.route_table.get(report.__class__.__name__, None)

    def add_dispatch_rule(self, report_type: type[Report], dispatch_rule: DispatchRule):
        """
        Add a dispatch rule for the given report type.
        :param report_type: The report type to which the dispatch rule should map to
        :param dispatch_rule: The dispatch rule to handle the reports of the given type
        """
        if dispatch_rule.is_primary:
            self.primary_dispatch_rule = dispatch_rule

        self.route_table[report_type.__name__] = dispatch_rule
