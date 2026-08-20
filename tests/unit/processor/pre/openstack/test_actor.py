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

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

pytest.importorskip('openstack')

from powerapi.actor import State
from powerapi.actor.message import PoisonPillMessage, StartMessage
from powerapi.processor.pre.openstack.actor import (
    OpenStackPreProcessorActor,
    OpenStackProcessorState,
)
from powerapi.processor.pre.openstack.handlers import (
    HWPCReportHandler,
    PoisonPillMessageHandler,
    StartMessageHandler,
)
from powerapi.report import HWPCReport


def test_processor_state_builds_metadata_components():
    """
    The processor state should initialize its manager, registry, and monitor agent.
    """
    monitor_config = Mock()

    with (
        patch('powerapi.processor.pre.openstack.actor.Manager'),
        patch('powerapi.processor.pre.openstack.actor.OpenStackMetadataRegistry') as metadata_registry_class,
        patch('powerapi.processor.pre.openstack.actor.OpenStackMonitorAgent') as monitor_agent_class,
    ):
        state = OpenStackProcessorState(Mock(), monitor_config)

    metadata_registry_class.assert_called_once_with(state.manager)
    monitor_agent_class.assert_called_once_with(state.metadata_registry, monitor_config)


@pytest.mark.parametrize(
    ('message', 'expected_handler_type'),
    [
        (StartMessage(), StartMessageHandler),
        (PoisonPillMessage(), PoisonPillMessageHandler),
        (HWPCReport(datetime.now(), 'pytest', 'pytest', {}), HWPCReportHandler),
    ],
    ids=['start_message', 'poison_pill_message', 'hwpc_report'],
)
def test_actor_setup_registers_openstack_handlers(message, expected_handler_type):
    """
    Actor setup should create its state and register OpenStack handlers.
    """
    monitor_config = Mock()
    actor = OpenStackPreProcessorActor('pytest', monitor_config)
    state = State(actor)

    with patch('powerapi.processor.pre.openstack.actor.OpenStackProcessorState', return_value=state):
        actor.setup()

    assert actor.state is state
    assert isinstance(state.get_corresponding_handler(message), expected_handler_type)
