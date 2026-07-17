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

pytest.importorskip('powerapi.database.clickhouse.driver')  # The ClickHouse driver requires external dependencies to work.

from powerapi.database.clickhouse.driver import ClickHouseOutputFactory


@pytest.fixture
def clickhouse_config() -> dict:
    """
    Fixture that provides a configuration with a ClickHouse pusher.
    """
    return {
        'stream': True,
        'verbose': True,
        'output': {
            'pytest-clickhouse-pusher': {
                'type': 'clickhouse',
                'model': 'PowerReport',
                'host': 'example.clickhouse.cloud',
                'port': 8443,
                'username': 'powerapi',
                'password': 'pytest-powerapi-password',
                'database': 'powerapi',
            },
        },
    }


def test_pusher_generator_with_valid_clickhouse_config(clickhouse_config):
    """
    PusherGenerator should generate a PusherActor with a ClickHouse database driver.
    """
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(clickhouse_config)

    assert len(pushers) == 1
    assert 'pytest-clickhouse-pusher' in pushers

    pusher = pushers['pytest-clickhouse-pusher']
    assert isinstance(pusher, PusherActor)

    db_factory = pusher.database_factory
    assert isinstance(db_factory, ClickHouseOutputFactory)

    expected_db_attributes = clickhouse_config['output']['pytest-clickhouse-pusher']
    assert db_factory.host == expected_db_attributes['host']
    assert db_factory.port == expected_db_attributes['port']
    assert db_factory.username == expected_db_attributes['username']
    assert db_factory.password == expected_db_attributes['password']
    assert db_factory.database_name == expected_db_attributes['database']


@pytest.mark.parametrize('missing_arg', ['model', 'host', 'port', 'username', 'password', 'database'])
def test_pusher_generator_with_missing_arguments_in_clickhouse_config(clickhouse_config, missing_arg):
    """
    PusherGenerator should raise an exception when a required argument is missing from the ClickHouse config.
    """
    generator = PusherGenerator()

    clickhouse_config['output']['pytest-clickhouse-pusher'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(clickhouse_config)
