# Copyright (c) 2022, Inria
# Copyright (c) 2022, University of Lille
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

import logging
import time

import pytest

from powerapi.pusher import PusherActor
from tests.unit.actor.abstract_test_actor import AbstractTestActorWithDB
from tests.utils.db import make_report, generate_reports


class TestPusher(AbstractTestActorWithDB):
    """
    Pusher actor tests.
    """

    @pytest.fixture
    def actor_with_db(self, request, fake_db):
        delay = 0.1
        buffer_size = 50
        if hasattr(request, "param"):
            delay = request.param.get("delay", delay)
            buffer_size = request.param.get("buffer_size", buffer_size)

        return PusherActor('pusher_test', fake_db, delay, buffer_size, logging.DEBUG)


def test_report_handler_save_reports_when_buffer_size_exceeded(pusher_report_handler, fake_database):
    """
    Test that report handler writes reports to database when buffer size is exceeded.
    """
    handler = pusher_report_handler(buffer_size=2, last_write_ts=float('inf'))

    report1 = make_report()
    handler.handle(report1)
    received_reports = fake_database.read()
    assert received_reports == []

    report2 = make_report()
    handler.handle(report2)
    received_reports = fake_database.read()
    assert received_reports == [report1, report2]


def test_report_handler_dont_save_reports_when_buffer_size_is_not_exceeded(pusher_report_handler, fake_database):
    """
    Test that report handler don't write reports to database when buffer size is not exceeded.
    """
    handler = pusher_report_handler(buffer_size=15, last_write_ts=float('inf'))

    reports_sent = generate_reports(10)
    for report in reports_sent:
        handler.handle(report)

    received_reports = fake_database.read()
    assert received_reports == []


def test_reading_reports_from_database_directly_after_sending_them_to_report_handler(pusher_report_handler, fake_database):
    """
    Test reading reports from database directly after sending them to the report handler.
    """
    handler = pusher_report_handler(buffer_size=0, last_write_ts=float('inf'))

    for report in generate_reports(10):
        handler.handle(report)
        received_reports = fake_database.read()
        assert received_reports == [report]


def test_report_handler_saves_all_reports_to_database_when_buffer_size_is_zero(pusher_report_handler, fake_database):
    """
    Test that report handler writes all reports to database when buffer size is zero.
    """
    handler = pusher_report_handler(buffer_size=0, last_write_ts=float('inf'))

    reports_sent = generate_reports(10)
    for report in reports_sent:
        handler.handle(report)

    reports_received = fake_database.read()
    assert reports_received == reports_sent


def test_report_handler_saves_report_to_database_when_flush_interval_is_exceeded(pusher_report_handler, fake_database):
    """
    Test that report handler writes the received report to the database when the flush interval is exceeded.
    """
    handler = pusher_report_handler(flush_interval=1.0, last_write_ts=0.0)

    report = make_report()
    handler.handle(report)

    received_reports = fake_database.read()
    assert received_reports == [report]


def test_report_handler_dont_save_reports_when_flush_interval_is_not_exceeded(pusher_report_handler, fake_database):
    """
    Test that report handler don't write reports to database when flush interval is not exceeded.
    """
    handler = pusher_report_handler(flush_interval=100.0, last_write_ts=time.monotonic())

    report = make_report()
    handler.handle(report)

    received_reports = fake_database.read()
    assert received_reports == []


def test_report_handler_follow_flush_interval_after_writing_to_database(pusher_report_handler, fake_database):
    """
    Test that report handler follows flush interval after writing a report to the database.
    """
    handler = pusher_report_handler(flush_interval=2.0, last_write_ts=time.monotonic())

    report1 = make_report()
    handler.handle(report1)
    received_reports = fake_database.read()
    assert received_reports == []

    time.sleep(handler.flush_interval * 1.15)

    report2 = make_report()
    handler.handle(report2)
    received_reports = fake_database.read()
    assert received_reports == [report1, report2]
