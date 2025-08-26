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

from powerapi.handler import StartHandler, PoisonPillMessageHandler
from powerapi.message import ErrorMessage
from powerapi.puller.database_poller import DatabasePollerThread


class PullerPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    PoisonPillMessage handler for the Puller actor.
    """

    def teardown(self, soft: bool = False) -> None:
        """
        Teardown the Puller actor.
        :param soft: Toggle soft-kill mode for the actor
        """
        if self.state.db_poller_thread and self.state.db_poller_thread.is_alive():
            self.state.db_poller_thread.stop()
            self.state.db_poller_thread.join(timeout=5.0)

        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.socket_interface.close()


class PullerStartMessageHandler(StartHandler):
    """
    StartMessage handler for the Puller actor.
    """

    def initialization(self) -> None:
        """
        Initialize the Puller actor.
        """
        if not self.state.report_filter.filters:
            self.state.actor.send_control(ErrorMessage('Report filter is empty'))
            return

        for _, dispatcher in self.state.report_filter.filters:
            dispatcher.connect_data()

        db_poller_thread = DatabasePollerThread(self.state.actor, self.state.database, self.state.report_filter, self.state.stream_mode)
        db_poller_thread.start()
        if not db_poller_thread.is_alive():
            self.state.actor.send_control(ErrorMessage('Database poller thread failed to start'))
            self.state.alive = False
            return

        self.state.db_poller_thread = db_poller_thread
