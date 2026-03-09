# Copyright (c) 2023, Inria
# Copyright (c) 2023, University of Lille
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

from powerapi.actor import StartMessage, PoisonPillMessage


def test_start_handler_empty_report_filter_kill_actor(puller_start_handler, empty_report_filter):
    """
    Test that start handler kills the actor when the report filter is empty.
    """
    handler = puller_start_handler(empty_report_filter)
    handler.handle(StartMessage())

    assert handler.state.alive is False


def test_start_handler_initializes_database_poller(puller_start_handler, broadcast_report_filter):
    """
    Test that start handler initializes the database poller.
    """
    handler = puller_start_handler(broadcast_report_filter)
    handler.handle(StartMessage())

    assert handler.state.alive is True
    handler.state.db_poller_thread.start.assert_called_once()


def test_start_handler_fail_initialize_database_poller_kill_actor(puller_start_handler, broadcast_report_filter):
    """
    Test that start handler kills the actor when the database poller fails to initialize.
    """
    handler = puller_start_handler(broadcast_report_filter)
    handler.state.db_poller_thread.start.side_effect = None
    handler.state.db_poller_thread.is_alive.return_value = False

    handler.handle(StartMessage())

    assert handler.state.alive is False
    handler.state.db_poller_thread.start.assert_called_once()


def test_poison_pill_handler_stop_database_poller(puller_poison_pill_handler):
    """
    Test that poison pill handler stops the database poller before killing the actor.
    """
    handler = puller_poison_pill_handler()
    handler.handle(PoisonPillMessage(soft=False))

    assert handler.state.alive is False
    handler.state.db_poller_thread.stop.assert_called_once()
    handler.state.db_poller_thread.join.assert_called_once()
