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

from powerapi.exception import PowerAPIException


class PrimaryDispatchRuleRuleAlreadyDefinedException(PowerAPIException):
    """
    Exception raised when trying to define a primary dispatch rule on a route table that have already one
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

        return None

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
