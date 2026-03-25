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

import pytest

pytest.importorskip('powerapi.processor.pre.k8s.actor')  # The Kubernetes processor requires external dependencies to work.

from powerapi.cli.generator import PreProcessorGenerator
from powerapi.exception import PowerAPIException
from powerapi.processor.pre.k8s.actor import K8sPreProcessorActor


@pytest.fixture
def k8s_processor_config():
    """
    Fixture that provides a configuration with a Kubernetes pre-processor.
    """
    return {
        'stream': True,
        'verbose': True,
        'pre-processor': {
            'pytest-k8s-preprocessor': {
                'type': 'k8s',
                'api-mode': 'manual',
                'api-host': 'https://127.0.0.1:36599',
                'api-key': 'pytest-token-powerapi',
                'puller': 'pytest-json-puller'
            }
        }
    }


def test_preprocessor_generator_with_valid_k8s_config(k8s_processor_config):
    """
    PreProcessorGenerator should generate a K8sPreProcessorActor.
    """
    generator = PreProcessorGenerator()
    preprocessors = generator.generate(k8s_processor_config)

    assert len(preprocessors) == 1
    assert 'pytest-k8s-preprocessor' in preprocessors

    preprocessor = preprocessors['pytest-k8s-preprocessor']
    assert isinstance(preprocessor, K8sPreProcessorActor)

    expected_preprocessor_attributes = k8s_processor_config['pre-processor']['pytest-k8s-preprocessor']
    assert preprocessor.config.api_mode == expected_preprocessor_attributes['api-mode']
    assert preprocessor.config.api_key == expected_preprocessor_attributes['api-key']
    assert preprocessor.config.api_host == expected_preprocessor_attributes['api-host']


@pytest.mark.parametrize('missing_arg', ['api-mode'])
def test_preprocessor_generator_with_missing_arguments_in_k8s_config(k8s_processor_config, missing_arg):
    """
    PreProcessorGenerator should raise an exception when a required argument is missing from the MongoDB config.
    """
    generator = PreProcessorGenerator()

    k8s_processor_config['pre-processor']['pytest-k8s-preprocessor'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(k8s_processor_config)
