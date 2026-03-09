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


def test_broadcast_report_filter_replace_registered_dispatcher():
    """
    Replacing a registered dispatcher must update both registered and routed dispatchers.
    """
    report_filter = BroadcastReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    report_filter.register(rule_always_true, dispatcher_a)

    dispatcher_b = Mock(name="dispatcher_b")
    report_filter.register(rule_always_true, dispatcher_b)

    dispatcher_c = Mock(name="dispatcher_c")
    report_filter.register(rule_always_true, dispatcher_c)

    dispatcher_x = Mock(name="dispatcher_x")
    report_filter.replace(dispatcher_a, dispatcher_x)

    assert list(report_filter.dispatchers()) == [dispatcher_x, dispatcher_b, dispatcher_c]
    assert list(report_filter.route(make_report())) == [dispatcher_x, dispatcher_b, dispatcher_c]


def test_broadcast_report_filter_replace_all_occurrences():
    """
    Replacing a dispatcher must affect every occurrence while preserving the ordering.
    """
    report_filter = BroadcastReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")
    dispatcher_x = Mock(name="dispatcher_x")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_true, dispatcher_b)
    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_true, dispatcher_a)

    report_filter.replace(dispatcher_a, dispatcher_x)

    assert list(report_filter.dispatchers()) == [dispatcher_x, dispatcher_b, dispatcher_x, dispatcher_x]
    assert list(report_filter.route(make_report())) == [dispatcher_x, dispatcher_b, dispatcher_x, dispatcher_x]


def test_broadcast_report_filter_replace_is_noop_for_unknown_dispatcher():
    """
    Replacing a non-registered dispatcher must not mutate a broadcast filter.
    """
    report_filter = BroadcastReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")
    dispatcher_unknown = Mock(name="dispatcher_unknown")
    dispatcher_x = Mock(name="dispatcher_x")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_true, dispatcher_b)
    size_before = len(report_filter)

    report_filter.replace(dispatcher_unknown, dispatcher_x)

    assert len(report_filter) == size_before
    assert list(report_filter.dispatchers()) == [dispatcher_a, dispatcher_b]
    assert list(report_filter.route(make_report())) == [dispatcher_a, dispatcher_b]


def test_broadcast_report_filter_replace_keeps_length_and_allows_duplicates():
    """
    Replacing with an already-registered dispatcher must keep the same filter size.
    """
    report_filter = BroadcastReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_true, dispatcher_b)
    report_filter.register(rule_always_true, dispatcher_a)
    size_before = len(report_filter)

    report_filter.replace(dispatcher_a, dispatcher_b)

    assert len(report_filter) == size_before
    assert list(report_filter.dispatchers()) == [dispatcher_b, dispatcher_b, dispatcher_b]
    assert list(report_filter.route(make_report())) == [dispatcher_b, dispatcher_b, dispatcher_b]


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


def test_ruleset_report_filter_replace_registered_dispatcher():
    """
    Replacing a registered dispatcher must only swap matching targets and keep rules.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    report_filter.register(rule_always_true, dispatcher_a)

    dispatcher_b = Mock(name="dispatcher_b")
    report_filter.register(rule_always_false, dispatcher_b)

    dispatcher_x = Mock(name="dispatcher_x")
    report_filter.replace(dispatcher_a, dispatcher_x)

    assert list(report_filter.dispatchers()) == [dispatcher_x, dispatcher_b]
    assert list(report_filter.route(make_report())) == [dispatcher_x]


def test_ruleset_report_filter_replace_all_occurrences():
    """
    Replacing a dispatcher in a ruleset filter must update every matching rule target.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")
    dispatcher_x = Mock(name="dispatcher_x")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_false, dispatcher_b)
    report_filter.register(rule_always_true, dispatcher_a)

    report_filter.replace(dispatcher_a, dispatcher_x)

    assert list(report_filter.dispatchers()) == [dispatcher_x, dispatcher_b, dispatcher_x]
    assert list(report_filter.route(make_report())) == [dispatcher_x, dispatcher_x]


def test_ruleset_report_filter_replace_is_noop_for_unknown_dispatcher():
    """
    Replacing a non-registered dispatcher must not mutate a ruleset filter.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")
    dispatcher_unknown = Mock(name="dispatcher_unknown")
    dispatcher_x = Mock(name="dispatcher_x")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_false, dispatcher_b)
    size_before = len(report_filter)

    report_filter.replace(dispatcher_unknown, dispatcher_x)

    assert len(report_filter) == size_before
    assert list(report_filter.dispatchers()) == [dispatcher_a, dispatcher_b]
    assert list(report_filter.route(make_report())) == [dispatcher_a]


def test_ruleset_report_filter_replace_keeps_rules_behavior():
    """
    Replacing a dispatcher must not alter predicate behavior.
    """
    report_filter = RulesetReportFilter()

    def match_sensor_a(report) -> bool:
        return report.sensor == "sensor_a"

    def match_sensor_b(report) -> bool:
        return report.sensor == "sensor_b"

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")
    dispatcher_x = Mock(name="dispatcher_x")

    report_filter.register(match_sensor_a, dispatcher_a)
    report_filter.register(match_sensor_b, dispatcher_b)

    report_filter.replace(dispatcher_a, dispatcher_x)

    assert list(report_filter.route(make_report(sensor="sensor_a"))) == [dispatcher_x]
    assert list(report_filter.route(make_report(sensor="sensor_b"))) == [dispatcher_b]
    assert list(report_filter.route(make_report(sensor="sensor_other"))) == []


def test_ruleset_report_filter_replace_keeps_length_and_allows_duplicates():
    """
    Replacing with an already-registered dispatcher must keep size and allow duplicates.
    """
    report_filter = RulesetReportFilter()

    dispatcher_a = Mock(name="dispatcher_a")
    dispatcher_b = Mock(name="dispatcher_b")

    report_filter.register(rule_always_true, dispatcher_a)
    report_filter.register(rule_always_false, dispatcher_b)
    report_filter.register(rule_always_true, dispatcher_a)
    size_before = len(report_filter)

    report_filter.replace(dispatcher_a, dispatcher_b)

    assert len(report_filter) == size_before
    assert list(report_filter.dispatchers()) == [dispatcher_b, dispatcher_b, dispatcher_b]
    assert list(report_filter.route(make_report())) == [dispatcher_b, dispatcher_b]
