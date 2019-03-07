# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import signal

from powerapi.actor import Supervisor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor

class BackendSupervisor(Supervisor):

    def __init__(self, stream_mode):
        super().__init__()

        #: (bool): Enable stream mode.
        self.stream_mode = stream_mode

        #: (list): List of Puller
        self.pullers = []

        #: (list): List of Dispatcher
        self.dispatchers = []

        #: (list): List of Pusher
        self.pushers = []

    def join(self):
        """
        wait until all actor are terminated
        """
        # List the different kind of actor
        for actor in self.supervised_actors:
            if isinstance(actor, PullerActor):
                self.pullers.append(actor)
            elif isinstance(actor, DispatcherActor):
                self.dispatchers.append(actor)
            else:
                self.pushers.append(actor)

        if self.stream_mode:
            self.join_stream_mode_on()
        else:
            self.join_stream_mode_off()

    def join_stream_mode_on(self):
        """
        Supervisor behaviour when stream mode is on.
        When end raise (for exemple by CRTL+C)
        -> Kill all actor in the following order (Puller - Dispatcher/Formula - Pusher)
            1. Send SIGTERM
            2. Join X seconds
            3. If still alive, send SIGKILL
            4. Join
        """
        def kill_behaviour(actor):
            actor.terminate()
            actor.join(5)
            if actor.is_alive():
                actor.kill()
                actor.join()

        # Setup signal handler
        def term_handler(_, __):
            pass

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        # Wait for signal
        signal.pause()

        for puller in self.pullers:
            kill_behaviour(puller)

        for dispatcher in self.dispatchers:
            kill_behaviour(dispatcher)

        for pusher in self.pushers:
            kill_behaviour(pusher)

    def join_stream_mode_off(self):
        """
        Supervisor behaviour when stream mode is off.
        - Supervisor wait the Puller death
        - Supervisor wait for the dispatcher death
        - Supervisor send a PoisonPill (by_data) to the Pusher
        - Supervisor wait for the Pusher death
        """
        for puller in self.pullers:
            puller.join()

        for dispatcher in self.dispatchers:
            dispatcher.join()

        for pusher in self.pushers:
            pusher.send_kill(by_data=True)

        for pusher in self.pushers:
            pusher.join()
