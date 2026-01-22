# Copyright (c) 2018, Inria
# Copyright (c) 2018, University of Lille
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

from abc import ABC, abstractmethod
from collections.abc import Sized, Iterable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from powerapi.actor import ActorProxy
    from powerapi.report import Report


class ReportRule(Protocol):
    """
    Abstract report rule class.
    Used to check if a report should be routed to a dispatcher.
    """

    def __call__(self, report: Report) -> bool: ...


class ReportFilter(ABC, Sized):
    """
    Abstract report filter class.
    Used by puller actors to filter and route reports to their(s) corresponding dispatcher(s).
    """

    @abstractmethod
    def register(self, rule: ReportRule, dispatcher: ActorProxy) -> None: ...

    @abstractmethod
    def route(self, report: Report) -> Iterable[ActorProxy]: ...

    @abstractmethod
    def dispatchers(self) -> Iterable[ActorProxy]: ...


class BroadcastReportFilter(ReportFilter):
    """
    Broadcast report filter class.
    No filtering capabilities are supported, the reports will be routed to all defined dispatcher(s).
    """

    def __init__(self):
        self._dispatchers: list[ActorProxy] = []

    def register(self, rule: ReportRule, dispatcher: ActorProxy) -> None:
        """
        Register a report filter.
        :param rule: Unused parameter, any value will be ignored
        :param dispatcher: Dispatcher where the report will be routed to
        """
        self._dispatchers.append(dispatcher)

    def route(self, report: Report) -> Iterable[ActorProxy]:
        """
        Returns the dispatchers where the given report should be sent to.
        :param report: Report to route
        :return: Iterable of dispatchers
        """
        return iter(self._dispatchers)

    def dispatchers(self) -> Iterable[ActorProxy]:
        """
        Returns all registered dispatchers.
        :return: Iterable of dispatchers
        """
        return iter(self._dispatchers)

    def __len__(self) -> int:
        return len(self._dispatchers)


class RulesetReportFilter(ReportFilter):
    """
    Ruleset report filter class.
    Allow to route reports to dispatcher(s) based on rules.
    """

    def __init__(self):
        self._filters: list[tuple[ReportRule, ActorProxy]] = []

    def register(self, rule: ReportRule, dispatcher: ActorProxy) -> None:
        """
        Register a new filter rule.
        :param rule: Predicate evaluated for each report
        :param dispatcher: Dispatcher where the report will be routed to if the rule matches
        """
        self._filters.append((rule, dispatcher))

    def route(self, report: Report) -> Iterable[ActorProxy]:
        """
        Returns the dispatchers where the given report should be sent to.
        :param report: Report to route
        :return: Iterable of dispatchers
        """
        return (dispatcher for rule, dispatcher in self._filters if rule(report))

    def dispatchers(self) -> Iterable[ActorProxy]:
        """
        Returns all registered dispatchers regardless of rules.
        :return: Iterable of dispatchers
        """
        return (dispatcher for _, dispatcher in self._filters)

    def __len__(self) -> int:
        return len(self._filters)
