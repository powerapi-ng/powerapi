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

from unittest.mock import Mock, call

from powerapi.actor import ActorProxy
from powerapi.puller.database_poller import DatabasePollerThread
from tests.utils.db import PrebuiltDatabaseFactory, generate_reports


def test_poller_broadcasts_reports_and_closes_connections(monkeypatch):
    """
    Test that the poller sends each report to every target in order and closes connections.
    """
    reports = generate_reports(2)
    database = Mock()
    database.read.return_value = reports
    targets = [Mock(spec=ActorProxy), Mock(spec=ActorProxy)]
    monkeypatch.setattr('powerapi.puller.database_poller.os.kill', Mock())
    poller = DatabasePollerThread(PrebuiltDatabaseFactory(database), targets, stream_mode=False)

    poller.run()

    database.connect.assert_called_once()
    database.read.assert_called_once_with(False)
    database.disconnect.assert_called_once()
    for target in targets:
        target.connect_data.assert_called_once_with()
        assert target.send_data.call_args_list == [call(report) for report in reports]
        target.disconnect.assert_called_once_with()
