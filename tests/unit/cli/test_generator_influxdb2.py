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

pytest.importorskip("powerapi.database.influxdb2")  # The InfluxDB2 driver requires external dependencies to work.

from powerapi.database.influxdb2 import InfluxDB2


@pytest.fixture
def influxdb2_config() -> dict:
    """
    Fixture that provides a configuration with an InfluxDB2 pusher.
    """
    return {
        'stream': True,
        'verbose': True,
        'output': {
            'pytest-influxdb2-pusher': {
                'type': 'influxdb2',
                'model': 'PowerReport',
                'uri': 'http://localhost:8086',
                'org': 'powerapi',
                'token': 'powerapi-auth-token',
                'bucket': 'powerapi-example-bucket',
                'tags': 'powerapi_example_tag1,powerapi_example_tag2'
            }
        }
    }


def test_pusher_generator_with_valid_influxdb2_config(influxdb2_config):
    """
    PusherGenerator should generate a PusherActor with an InfluxDB2 database driver.
    """
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(influxdb2_config)

    assert len(pushers) == 1
    assert 'pytest-influxdb2-pusher' in pushers

    pusher = pushers['pytest-influxdb2-pusher']
    assert isinstance(pusher, PusherActor)

    db = pusher.database
    assert isinstance(db, InfluxDB2)

    expected_db_attributes = influxdb2_config['output']['pytest-influxdb2-pusher']
    assert db._client.url == expected_db_attributes['uri']
    assert db._client.org == expected_db_attributes['org']
    assert db._client.token == expected_db_attributes['token']
    assert db._bucket_name == expected_db_attributes['bucket']


@pytest.mark.parametrize('missing_arg', ['model', 'uri', 'org', 'token', 'bucket'])
def test_pusher_generator_with_missing_arguments_in_influxdb2_config(influxdb2_config, missing_arg):
    """
    PusherGenerator should raise an exception when a required argument is missing from the InfluxDB2 config.
    """
    generator = PusherGenerator()

    influxdb2_config['output']['pytest-influxdb2-pusher'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(influxdb2_config)
