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

from powerapi.cli.generator import PusherGenerator, PullerGenerator
from powerapi.exception import PowerAPIException
from powerapi.filter import BroadcastReportFilter
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor

pytest.importorskip('powerapi.database.mongodb')  # The MongoDB driver requires external dependencies to work.

from powerapi.database.mongodb import MongodbOutput, MongodbInput


@pytest.fixture
def mongodb_config() -> dict:
    """
    Fixture that provides a configuration with a MongoDB puller and pusher.
    """
    return {
        'stream': True,
        'verbose': True,
        'input': {
            'pytest-mongodb-puller': {
                'type': 'mongodb',
                'model': 'HWPCReport',
                'uri': 'mongodb://localhost:27017/',
                'db': 'pytest-powerapi',
                'collection': 'hwpc-report-input'
            }
        },
        'output': {
            'pytest-mongodb-pusher': {
                'type': 'mongodb',
                'model': 'PowerReport',
                'uri': 'mongodb://localhost:27017/',
                'db': 'pytest-powerapi',
                'collection': 'power-report-output'
            }
        }
    }


def test_puller_generator_with_valid_mongodb_config(mongodb_config):
    """
    PullerGenerator should generate a PullerActor with a MongoDB database driver.
    """
    puller_generator = PullerGenerator(BroadcastReportFilter())
    pullers = puller_generator.generate(mongodb_config)

    assert len(pullers) == 1
    assert 'pytest-mongodb-puller' in pullers

    puller = pullers['pytest-mongodb-puller']
    assert isinstance(puller, PullerActor)

    db = puller.database
    assert isinstance(db, MongodbInput)

    expected_db_attributes = mongodb_config['input']['pytest-mongodb-puller']
    assert db.uri == expected_db_attributes['uri']
    assert db.database_name == expected_db_attributes['db']
    assert db.collection_name == expected_db_attributes['collection']


@pytest.mark.parametrize('missing_arg', ['model', 'uri'])
def test_puller_generator_with_missing_arguments_in_mongodb_config(mongodb_config, missing_arg):
    """
    PullerGenerator should raise an exception when a required argument is missing from the MongoDB config.
    """
    generator = PullerGenerator(BroadcastReportFilter())

    mongodb_config['input']['pytest-mongodb-puller'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(mongodb_config)


def test_pusher_generator_with_valid_mongodb_config(mongodb_config):
    """
    PusherGenerator should generate a PusherActor with a MongoDB database driver.
    """
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(mongodb_config)

    assert len(pushers) == 1
    assert 'pytest-mongodb-pusher' in pushers

    pusher = pushers['pytest-mongodb-pusher']
    assert isinstance(pusher, PusherActor)

    db = pusher.database
    assert isinstance(db, MongodbOutput)

    expected_db_attributes = mongodb_config['output']['pytest-mongodb-pusher']
    assert db.uri == expected_db_attributes['uri']
    assert db.database_name == expected_db_attributes['db']
    assert db.collection_name == expected_db_attributes['collection']


@pytest.mark.parametrize('missing_arg', ['model', 'uri', 'db', 'collection'])
def test_pusher_generator_with_missing_arguments_in_mongodb_config(mongodb_config, missing_arg):
    """
    PusherGenerator should raise an exception when a required argument is missing from the MongoDB config.
    """
    generator = PusherGenerator()

    mongodb_config['output']['pytest-mongodb-pusher'].pop(missing_arg)

    with pytest.raises(PowerAPIException):
        generator.generate(mongodb_config)
