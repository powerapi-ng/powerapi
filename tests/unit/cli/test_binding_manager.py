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

from unittest.mock import Mock

import pytest

from powerapi.actor import ActorProxy
from powerapi.cli.binding_manager import PreProcessorBindingManager
from powerapi.cli.generator import PreProcessorGenerator, PullerGenerator
from powerapi.dispatcher import DispatcherActor
from powerapi.exception import UnexistingActorException, UnsupportedActorTypeException, TargetActorAlreadyUsed
from powerapi.filter import BroadcastReportFilter
from powerapi.processor.processor_actor import PreProcessorActor, ProcessorActor
from powerapi.puller import PullerActor


class NoopPreprocessor(PreProcessorActor):
    """
    Pre-processor actor that does nothing, for testing purposes.
    """


@pytest.fixture
def preprocessor_config():
    """
    Fixture that provides a configuration with a socket puller and a no-op pre-processor.
    """
    return {
        'verbose': True,
        'stream': True,
        'input': {
            'pytest-socket-puller': {
                'type': 'socket',
                'model': 'HWPCReport',
                'host': 'localhost',
                'port': 8889
            }
        },
        'pre-processor': {
            'pytest-noop-preprocessor': {
                'type': 'noop',
                'puller': 'pytest-socket-puller'
            }
        }
    }


@pytest.fixture
def puller_generator() -> PullerGenerator:
    """
    Fixture that provides a generator for the puller actors.
    """
    report_filter = BroadcastReportFilter()
    report_filter.register(lambda _: True, Mock(actor_name='pytest-dispatcher', actor_type=DispatcherActor, spec=ActorProxy))

    generator = PullerGenerator(report_filter)
    return generator


@pytest.fixture
def preprocessor_generator() -> PreProcessorGenerator:
    """
    Fixture to return a preprocessor generator with the noop preprocessor available.
    """
    generator = PreProcessorGenerator()

    def _noop_processor_factory(_) -> ProcessorActor:
        return NoopPreprocessor('pytest-noop-preprocessor')

    generator.add_processor_factory('noop', _noop_processor_factory)
    return generator


def test_preprocessor_binding_manager_replace_puller_target(puller_generator, preprocessor_generator, preprocessor_config):
    """
    The binding manager should replace the target of the puller actor from a dispatcher actor to the pre-processor actor.
    """
    pullers = puller_generator.generate(preprocessor_config)
    processors = preprocessor_generator.generate(preprocessor_config)
    binding_manager = PreProcessorBindingManager(preprocessor_config, pullers, processors)

    puller = pullers['pytest-socket-puller']
    assert isinstance(puller, PullerActor)

    puller_target_proxy, = puller.report_filter.dispatchers()
    assert issubclass(puller_target_proxy.actor_type, DispatcherActor)
    assert puller_target_proxy.actor_name == 'pytest-dispatcher'

    binding_manager.process_bindings()

    puller_target_proxy, = puller.report_filter.dispatchers()
    assert issubclass(puller_target_proxy.actor_type, PreProcessorActor)
    assert puller_target_proxy.actor_name == 'pytest-noop-preprocessor'


def test_preprocessor_binding_manager_with_empty_preprocessor_config(puller_generator, preprocessor_config):
    """
    The binding manager should not replace the target of the puller actor when there is no pre-processor configuration.
    """
    preprocessor_config['pre-processor'] = {}

    pullers = puller_generator.generate(preprocessor_config)
    processors = {}
    binding_manager = PreProcessorBindingManager(preprocessor_config, pullers, processors)

    puller = pullers['pytest-socket-puller']
    assert isinstance(puller, PullerActor)

    puller_target_proxy, = puller.report_filter.dispatchers()
    assert issubclass(puller_target_proxy.actor_type, DispatcherActor)
    assert puller_target_proxy.actor_name == 'pytest-dispatcher'

    binding_manager.process_bindings()

    puller_target_proxy, = puller.report_filter.dispatchers()
    assert issubclass(puller_target_proxy.actor_type, DispatcherActor)
    assert puller_target_proxy.actor_name == 'pytest-dispatcher'


def test_preprocessor_binding_manager_with_invalid_puller_name(puller_generator, preprocessor_generator, preprocessor_config):
    """
    The binding manager should raise an exception when the puller name of the pre-processor is invalid.
    """
    preprocessor_config['pre-processor']['pytest-noop-preprocessor']['puller'] = 'invalid-puller-target'

    pullers = puller_generator.generate(preprocessor_config)
    processors = preprocessor_generator.generate(preprocessor_config)
    binding_manager = PreProcessorBindingManager(preprocessor_config, pullers, processors)

    with pytest.raises(UnexistingActorException):
        binding_manager.process_bindings()


def test_preprocessor_binding_manager_with_invalid_puller_type(puller_generator, preprocessor_generator, preprocessor_config):
    """
    The binding manager should raise an exception when the puller type of the pre-processor is invalid.
    """
    pullers = puller_generator.generate(preprocessor_config)
    pullers['pytest-socket-puller'] = Mock(name='pytest-socket-puller')

    processors = preprocessor_generator.generate(preprocessor_config)
    binding_manager = PreProcessorBindingManager(preprocessor_config, pullers, processors)

    with pytest.raises(UnsupportedActorTypeException):
        binding_manager.process_bindings()


def test_preprocessor_binding_manager_with_duplicate_target(puller_generator, preprocessor_generator, preprocessor_config):
    """
    The binding manager should raise an exception when multiple pre-processor have the same target.
    """
    pre_processors = preprocessor_config['pre-processor']
    pre_processors['pytest-noop-preprocessor-duplicate'] = pre_processors['pytest-noop-preprocessor']

    pullers = puller_generator.generate(preprocessor_config)
    processors = preprocessor_generator.generate(preprocessor_config)
    binding_manager = PreProcessorBindingManager(preprocessor_config, pullers, processors)

    with pytest.raises(TargetActorAlreadyUsed):
        binding_manager.process_bindings()
