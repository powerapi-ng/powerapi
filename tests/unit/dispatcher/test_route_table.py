# Copyright (c) 2026, Inria
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

from datetime import datetime

from powerapi.dispatch_rule import DispatchRule
from powerapi.dispatcher import RouteTable
from powerapi.report import Report


class ReportTypeA(Report):
    """
    Fake report type used to validate RouteTable mappings.
    """

    def __init__(self):
        super().__init__(timestamp=datetime.now(), sensor='sensor-a', target='target-a')


class ReportTypeB(Report):
    """
    Another fake report type used to validate RouteTable mappings.
    """

    def __init__(self):
        super().__init__(timestamp=datetime.now(), sensor='sensor-b', target='target-b')


class FakeDispatchRule(DispatchRule):
    """
    Minimal dispatch rule used for unit tests.
    """

    def __init__(self, primary: bool = False):
        super().__init__(primary=primary, fields=['sensor'])

    def get_formula_id(self, report: Report):
        return [(report.sensor,)]


def test_add_dispatch_rule_registers_rule_for_report_type():
    """
    Added rules should be retrievable for matching report types.
    """
    route_table = RouteTable()
    dispatch_rule = FakeDispatchRule()

    route_table.add_dispatch_rule(ReportTypeA, dispatch_rule)

    assert route_table.get_dispatch_rule(ReportTypeA()) is dispatch_rule


def test_get_dispatch_rule_returns_none_for_unknown_report_type():
    """
    Looking up an unregistered report type should return None.
    """
    route_table = RouteTable()

    assert route_table.get_dispatch_rule(ReportTypeA()) is None


def test_add_primary_dispatch_rule_sets_primary_dispatch_rule_attribute():
    """
    Adding a primary rule should update the primary_dispatch_rule attribute.
    """
    route_table = RouteTable()
    primary_rule = FakeDispatchRule(primary=True)

    route_table.add_dispatch_rule(ReportTypeA, primary_rule)

    assert route_table.primary_dispatch_rule is primary_rule


def test_add_non_primary_dispatch_rule_does_not_overwrite_existing_primary():
    """
    Non-primary rules should not overwrite an existing primary_dispatch_rule.
    """
    route_table = RouteTable()
    primary_rule = FakeDispatchRule(primary=True)
    secondary_rule = FakeDispatchRule(primary=False)

    route_table.add_dispatch_rule(ReportTypeA, primary_rule)
    route_table.add_dispatch_rule(ReportTypeB, secondary_rule)

    assert route_table.primary_dispatch_rule is primary_rule


def test_add_primary_dispatch_rule_overwrites_previous_primary():
    """
    The latest primary rule added should become the primary_dispatch_rule.
    """
    route_table = RouteTable()
    first_primary = FakeDispatchRule(primary=True)
    second_primary = FakeDispatchRule(primary=True)

    route_table.add_dispatch_rule(ReportTypeA, first_primary)
    route_table.add_dispatch_rule(ReportTypeB, second_primary)

    assert route_table.primary_dispatch_rule is second_primary


def test_add_dispatch_rule_overwrites_existing_mapping_for_same_report_type():
    """
    Re-registering a rule for the same report type should replace the previous mapping.
    """
    route_table = RouteTable()
    first_rule = FakeDispatchRule()
    second_rule = FakeDispatchRule()

    route_table.add_dispatch_rule(ReportTypeA, first_rule)
    route_table.add_dispatch_rule(ReportTypeA, second_rule)

    assert route_table.get_dispatch_rule(ReportTypeA()) is second_rule
