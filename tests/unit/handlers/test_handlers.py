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

import pytest
from mock import Mock

from powerapi.handler import PoisonPillMessageHandler
from powerapi.message import PoisonPillMessage

############
# Fixtures #
############
@pytest.fixture()
def mocked_ppHandler():
    """
    return a mocked PoisonPillMessageHandler
    """

    state = Mock()
    state.actor = Mock()
    state.actor.socket_interface = Mock()
    state.actor.socket_interface.receive = Mock(return_value=None)

    handler = PoisonPillMessageHandler(state)
    handler.teardown = Mock()
    return handler


def test_PoisonPillMessageHandler_soft(mocked_ppHandler):
    """
    handle a soft PoisonPillMessage with the handler

    Test if:
      - the receive method was called
      - the handler teardown method was called
    """

    mocked_ppHandler.handle(PoisonPillMessage(soft=True))
    assert mocked_ppHandler.state.actor.socket_interface.receive.called
    assert mocked_ppHandler.teardown.called


def test_PoisonPillMessageHandler_hard(mocked_ppHandler):
    """
    handle a hard PoisonPillMessage with the handler

    Test if:
      - the handler teardown method was called
    """

    mocked_ppHandler.handle(PoisonPillMessage(soft=False))
    assert mocked_ppHandler.teardown.called
