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

from powerapi.cli.generator import PusherGenerator
from powerapi.exception import PowerAPIException
from powerapi.pusher import PusherActor

pytest.importorskip("powerapi.database.prometheus")  # The Prometheus driver requires external dependencies to work.

from powerapi.database.prometheus import Prometheus


@pytest.fixture
def prometheus_config() -> dict:
    """
    Fixture that provides a configuration with a Prometheus pusher.
    """
    return {
        'stream': True,
        'verbose': True,
        'output': {
            'pytest-prometheus-pusher': {
                'type': 'prometheus',
                'model': 'PowerReport',
                'addr': 'localhost',
                'port': 8000,
                'tags': 'powerapi_example_tag1,powerapi_example_tag2'
            }
        }
    }

def test_pusher_generator_with_valid_prometheus_config(prometheus_config):
    """
    PusherGenerator should generate a PusherActor with a Prometheus database driver.
    """
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(prometheus_config)

    assert len(pushers) == 1
    assert 'pytest-prometheus-pusher' in pushers

    pusher = pushers['pytest-prometheus-pusher']
    assert isinstance(pusher, PusherActor)

    db = pusher.database
    assert isinstance(db, Prometheus)

    expected_db_attributes = prometheus_config['output']['pytest-prometheus-pusher']
    assert db.listen_addr == (expected_db_attributes['addr'], expected_db_attributes['port'])
    assert {'powerapi_example_tag1', 'powerapi_example_tag2'}.issubset(db.dynamic_tags)
    assert {'sensor', 'target', 'powerapi_example_tag1', 'powerapi_example_tag2'}.issubset(db.metric_labels)


@pytest.mark.parametrize('missing_arg', ['model', 'addr', 'port'])
def test_pusher_generator_with_missing_arguments_in_mongodb_config(prometheus_config, missing_arg):
    """
    PusherGenerator should raise an exception when a required argument is missing from the Prometheus config.
    """
    generator = PusherGenerator()

    prometheus_config['output']['pytest-prometheus-pusher'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(prometheus_config)
