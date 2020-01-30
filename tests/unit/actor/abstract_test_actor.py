# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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
import time

import pytest
from powerapi.message import PoisonPillMessage, StartMessage, OKMessage, ErrorMessage

class AbstractTestActor:

    @pytest.fixture
    def init_actor(self, actor):
        actor.start()
        actor.connect_data()
        actor.connect_control()
        yield actor
        if actor.is_alive():
            actor.terminate()
        actor.socket_interface.close()

    @pytest.fixture
    def started_actor(self, init_actor):
        init_actor.send_control(StartMessage())
        _ = init_actor.receive_control(2000)
        return init_actor

    def test_new_actor_is_alive(self, init_actor):
        assert init_actor.is_alive()

    def test_send_PoisonPillMessage_set_actor_alive_to_False(self, init_actor):
        init_actor.send_control(PoisonPillMessage())
        time.sleep(0.1)
        assert not init_actor.is_alive()

    def test_send_StartMessage_answer_OkMessage(self, init_actor):
        init_actor.send_control(StartMessage())
        msg = init_actor.receive_control(2000)
        print(msg)
        assert isinstance(msg, OKMessage)

    def test_send_StartMessage_to_already_started_actor_answer_ErrorMessage(self, started_actor):
        started_actor.send_control(StartMessage())
        msg = started_actor.receive_control(2000)
        assert isinstance(msg, ErrorMessage)
        assert msg.error_message == 'Actor already initialized'
