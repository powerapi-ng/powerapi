# Copyright (c) 2018, INRIA
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

import select

from powerapi.actor import Supervisor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor
from powerapi.pusher import PusherActor


class BackendSupervisor(Supervisor):
    """
    Provide additional functionality to deal with actors: join
    """

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

        #: (list): List of pre processors
        self.pre_processors = []

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
            elif isinstance(actor, PusherActor):
                self.pushers.append(actor)
            else:
                self.pre_processors.append(actor)

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
        for actor in self.supervised_actors:
            if not actor.is_alive():
                self.kill_actors()
                return

        actor_sentinels = [actor.sentinel for actor in self.supervised_actors]

        select.select(actor_sentinels, actor_sentinels, actor_sentinels)
        self.kill_actors()

    def join_stream_mode_off(self):
        """
        Supervisor behaviour when stream mode is off.
        - Supervisor wait the Puller death
        - Supervisor wait the pre-processors death
        - Supervisor wait for the dispatcher death
        - Supervisor send a PoisonPill (by_data) to the Pusher
        - Supervisor wait for the Pusher death
        """
        for puller in self.pullers:
            puller.join()
        for pre_processor in self.pre_processors:
            pre_processor.soft_kill()
            pre_processor.join()
        for dispatcher in self.dispatchers:
            dispatcher.soft_kill()
            dispatcher.join()
        for pusher in self.pushers:
            pusher.soft_kill()
            pusher.join()
