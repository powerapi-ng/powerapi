# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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

# pylint: disable=no-self-use,arguments-differ,unused-argument

from time import sleep
import pytest
from mock.mock import patch

from powerapi.processor.pre.libvirt.libvirt_pre_processor_actor import LibvirtPreProcessorActor
from powerapi.report import Report
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe
from tests.utils.actor.dummy_actor import DummyActor
from tests.utils.libvirt import REGEXP, LIBVIRT_TARGET_NAME1, UUID_1, MockedLibvirt, LIBVIRT_TARGET_NAME2


BAD_TARGET = 'lkjqlskjdlqksjdlkj'
DISPATCHER_NAME = 'test_libvirt_processor_dispatcher'
REPORT_TYPE_TO_BE_SENT = Report


class TestLibvirtProcessor(AbstractTestActor):
    """
    Class to test the processor related to libvirt
    """
    @pytest.fixture
    def started_fake_dispatcher(self, dummy_pipe_in):
        """
        Return a started DummyActor. When the test is finished, the actor is stopped
        """
        dispatcher = DummyActor(name=DISPATCHER_NAME, pipe=dummy_pipe_in, message_type=REPORT_TYPE_TO_BE_SENT)
        dispatcher.start()

        yield dispatcher
        if dispatcher.is_alive():
            dispatcher.terminate()

    @pytest.fixture
    def actor(self, started_fake_dispatcher):
        with patch('powerapi.processor.pre.libvirt.libvirt_pre_processor_actor.openReadOnly',
                   return_value=MockedLibvirt()):
            return LibvirtPreProcessorActor(name='processor_actor', uri='', regexp=REGEXP,
                                            target_actors=[started_fake_dispatcher])

    @pytest.mark.skip(reason='libvirt is disable by default')
    def test_modify_report_that_not_match_regexp_must_not_modify_report(self, started_actor,
                                                                        dummy_pipe_out,
                                                                        shutdown_system):
        """
        Test that te LibvirtProcessorActor does not modify an report that does not match the regexp
        """
        report = Report(0, 'sensor', BAD_TARGET)
        started_actor.send_data(msg=report)
        sleep(1)
        assert recv_from_pipe(dummy_pipe_out, 2) == (DISPATCHER_NAME, report)

    @pytest.mark.skip(reason='libvirt is disable by default')
    def test_modify_report_that_match_regexp_must_modify_report(self, started_actor, dummy_pipe_out, shutdown_system):
        """
        Test that a report matching the regexp of the processor is actually modified
        """
        report = Report(0, 'sensor', LIBVIRT_TARGET_NAME1)
        started_actor.send_data(msg=report)
        new_report = recv_from_pipe(dummy_pipe_out, 2)[1]
        assert new_report.metadata["domain_id"] == UUID_1

    @pytest.mark.skip(reason='libvirt is disable by default')
    def test_modify_report_that_match_regexp_but_with_wrong_domain_name_must_not_modify_report(self, started_actor,
                                                                                               dummy_pipe_out,
                                                                                               shutdown_system):
        """
        Test that a report matching the regexp but with wrong domain name is not modified by the processor
        """
        report = Report(0, 'sensor', LIBVIRT_TARGET_NAME2)
        started_actor.send_data(msg=report)
        sleep(1)
        assert recv_from_pipe(dummy_pipe_out, 2) == (DISPATCHER_NAME, report)
