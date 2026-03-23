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

pytest.importorskip('powerapi.processor.pre.openstack.actor')  # The OpenStack processor requires external dependencies to work.

from powerapi.cli.generator import PreProcessorGenerator
from powerapi.processor.pre.openstack.actor import OpenStackPreProcessorActor


@pytest.fixture
def openstack_config():
    """
    Fixture that provides a configuration with an OpenStack pre-processor.
    """
    return {
        'stream': True,
        'verbose': True,
        'pre-processor': {
            'pytest-openstack-preprocessor': {
                'type': 'openstack',
                'puller': 'pytest-json-puller'
            }
        }
    }


def test_preprocessor_generator_with_valid_openstack_config(openstack_config):
    """
    PreProcessorGenerator should generate an OpenStackPreProcessorActor when given a valid config.
    """
    generator = PreProcessorGenerator()
    preprocessors = generator.generate(openstack_config)

    assert len(preprocessors) == 1
    assert 'pytest-openstack-preprocessor' in preprocessors

    preprocessor = preprocessors['pytest-openstack-preprocessor']
    assert isinstance(preprocessor, OpenStackPreProcessorActor)
