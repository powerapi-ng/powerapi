# Copyright (c) 2025, Inria
# Copyright (c) 2025, University of Lille
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

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from powerapi.pusher.handlers import ReportHandler, PusherStartHandler, PusherPoisonPillMessageHandler
from powerapi.pusher.pusher_actor import PusherState

if TYPE_CHECKING:
    from tests.utils.db import FailingLocalQueueDatabase


@pytest.fixture
def pusher_start_handler(make_fake_failing_database):
    """
    Factory fixture for creating a pusher start handler.
    """
    def _create_handler(fail_connect: bool = False, fail_read: bool = False, fail_write: bool = False) -> tuple[PusherStartHandler, FailingLocalQueueDatabase]:
        db = make_fake_failing_database(fail_connect=fail_connect, fail_read=fail_read, fail_write=fail_write)
        state = PusherState(Mock(), db)
        handler = PusherStartHandler(state)
        return handler, db

    return _create_handler


@pytest.fixture
def pusher_poison_pill_handler(make_fake_failing_database):
    """
    Factory fixture for creating a pusher poison-pill handler.
    """
    def _create_handler(fail_connect: bool = False, fail_read: bool = False, fail_write: bool = False) -> tuple[PusherPoisonPillMessageHandler, FailingLocalQueueDatabase]:
        db = make_fake_failing_database(fail_connect=fail_connect, fail_read=fail_read, fail_write=fail_write)
        actor = Mock()
        actor.socket_interface.receive.return_value = None  # Prevents an infinite loop when triggering a graceful shutdown.
        state = PusherState(Mock(), db)
        handler = PusherPoisonPillMessageHandler(state)
        return handler, db

    return _create_handler


@pytest.fixture
def pusher_report_handler(make_fake_failing_database):
    """
    Factory fixture for creating a pusher report handler.
    """
    def _create_handler(flush_interval: float = 1.0, buffer_size: int = 10, last_write_ts: float = 0.0) -> tuple[ReportHandler, FailingLocalQueueDatabase]:
        db = make_fake_failing_database()
        state = PusherState(Mock(), db)
        handler = ReportHandler(state, flush_interval, buffer_size)
        handler._last_write_ts = last_write_ts
        return handler, db

    return _create_handler
