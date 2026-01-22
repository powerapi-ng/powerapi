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

from unittest.mock import Mock

from powerapi.filter import BroadcastReportFilter, RulesetReportFilter
from tests.utils.db import make_report


def rule_always_true(_) -> bool:
    """
    Report rule used in tests that always returns True.
    """
    return True


def rule_always_false(_) -> bool:
    """
    Report rule used in tests that always returns False.
    """
    return False


def test_broadcast_report_filter_routes_to_all_dispatchers():
    """
    Broadcast filters must forward every report to every registered dispatcher.
    """
    report_filter = BroadcastReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    report_filter.register(rule_always_true, dispatcher_a)

    dispatcher_b = Mock(name="dispatcher_b")
    report_filter.register(rule_always_true, dispatcher_b)

    dispatchers = report_filter.route(make_report())
    assert list(dispatchers) == [dispatcher_a, dispatcher_b]


def test_broadcast_report_filter_returns_empty_when_no_dispatchers():
    """
    Broadcast filters must return an empty list when no dispatchers are registered.
    """
    report_filter = BroadcastReportFilter()

    dispatchers = report_filter.route(make_report())
    assert list(dispatchers) == []


def test_ruleset_report_filter_routes_only_matching_dispatchers():
    """
    Ruleset filters must return dispatchers whose rules evaluate to True.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    report_filter.register(rule_always_true, dispatcher_a)

    dispatcher_b = Mock(name="dispatcher_b")
    report_filter.register(rule_always_false, dispatcher_b)

    dispatcher_c = Mock(name="dispatcher_c")
    report_filter.register(rule_always_true, dispatcher_c)

    dispatchers = report_filter.route(make_report())
    assert list(dispatchers) == [dispatcher_a, dispatcher_c]


def test_ruleset_report_filter_returns_empty_when_no_rules_match():
    """
    Ruleset filters must return an empty list when no rules match.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    report_filter.register(rule_always_false, dispatcher_a)

    dispatchers = report_filter.route(make_report())
    assert list(dispatchers) == []
