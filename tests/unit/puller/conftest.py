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

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from powerapi.filter import BroadcastReportFilter
from powerapi.puller.handlers import PullerStartMessageHandler, PullerPoisonPillMessageHandler
from powerapi.puller.puller_actor import PullerState

if TYPE_CHECKING:
    from powerapi.filter import ReportFilter


@pytest.fixture
def empty_report_filter():
    """
    Fixture for an empty report filter.
    """
    return BroadcastReportFilter()


@pytest.fixture
def broadcast_report_filter():
    """
    Fixture for a non-empty broadcast report filter.
    """
    report_filter = BroadcastReportFilter()
    report_filter.register(lambda _: True, Mock(name="dispatcher_a"))
    report_filter.register(lambda _: True, Mock(name="dispatcher_b"))
    report_filter.register(lambda _: True, Mock(name="dispatcher_c"))

    return report_filter


@pytest.fixture
def fake_database_poller():
    """
    Fixture for a fake database poller.
    """
    db_poller = Mock()

    def set_is_alive_flag():
        db_poller.is_alive.return_value = True

    def unset_is_alive_flag():
        db_poller.is_alive.return_value = False

    db_poller.start.side_effect = set_is_alive_flag
    db_poller.stop.side_effect = unset_is_alive_flag
    return db_poller


@pytest.fixture
def puller_start_handler(make_fake_failing_database, fake_database_poller):
    """
    Factory fixture for creating a puller start handler.
    """
    def _create_handler(report_filter: ReportFilter) -> PullerStartMessageHandler:
        actor = Mock()
        database = make_fake_failing_database()

        state = PullerState(actor, database, report_filter, stream_mode=False)
        state.db_poller_thread = fake_database_poller

        handler = PullerStartMessageHandler(state)
        return handler

    return _create_handler


@pytest.fixture
def puller_poison_pill_handler(make_fake_failing_database, empty_report_filter, fake_database_poller):
    """
    Factory fixture for creating a puller poison-pill handler.
    """
    def _create_handler() -> PullerPoisonPillMessageHandler:
        actor = Mock()
        actor.socket_interface.receive.return_value = None  # Prevents an infinite loop when triggering a graceful shutdown.

        database = make_fake_failing_database()

        state = PullerState(actor, database, empty_report_filter, stream_mode=False)
        state.db_poller_thread = fake_database_poller

        handler = PullerPoisonPillMessageHandler(state)
        return handler

    return _create_handler
