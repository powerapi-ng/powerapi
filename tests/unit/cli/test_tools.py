# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import pytest
import sys

from mock import Mock, patch

from powerapi.cli.generator import PullerGenerator, PusherGenerator, DBActorGenerator
from powerapi.cli.generator import ModelNameDoesNotExist, DatabaseNameDoesNotExist
from powerapi.puller import PullerActor
from powerapi.database import MongoDB
from powerapi.message import PullerStartMessage, PusherStartMessage

####################
# PULLER GENERATOR #
####################

class SysExitException(Exception):
    pass


@patch('sys.exit', side_effect=SysExitException())
def test_generate_puller_from_empty_config_dict_call_sys_exit(mocked_sys_exit):
    args = {}
    generator = PullerGenerator(None, [])

    with pytest.raises(SysExitException):
        generator.generate(args)


def test_generate_puller_from_simple_config():
    """
    generate mongodb puller from this config :
    { 'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'tutu'}}}

    Test if :
      - function return a dict containing one element, its key is 'toto'
      - puller type is PullerActor
      - puller name is toto
      - puller database type is MongoDB
      - database uri is titi
      - database db is tata
      - database collection is tutu

    """
    args = {'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi',
                                                                   'db': 'tata', 'collection': 'tutu'}}}
    generator = PullerGenerator(None, [])
    result = generator.generate(args)

    assert len(result) == 1
    assert 'toto' in result
    puller_cls, start_message = result['toto']
    assert puller_cls == PullerActor
    assert isinstance(start_message, PullerStartMessage)
    assert start_message.name == 'toto'

    db = start_message.database

    assert isinstance(db, MongoDB)
    assert db.uri == 'titi'
    assert db.db_name == 'tata'
    assert db.collection_name == 'tutu'


def test_generate_two_pusher():
    """
    generate two mongodb puller from this config :
    { 'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'tutu'},
                                                             'titi': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'huhu'}}}

    Test if :
      - function return a dict containing two actor, their key are 'toto' and 'titi'
      - pullers type are PullerActor
      - pullers name are toto and titi
      - pullers database type are MongoDB
      - databases uri are titi
      - databases db are tata
      - databases collection are tutu and huhu

    """
    args = {'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb',
                                                                'uri': 'titi', 'db': 'tata', 'collection': 'tutu'},
                                                       'titi': {'model': 'HWPCReport', 'type': 'mongodb',
                                                                'uri': 'titi', 'db': 'tata', 'collection': 'huhu'}}}
    generator = PullerGenerator(None, [])
    result = generator.generate(args)

    assert len(result) == 2
    assert 'toto' in result
    puller1_cls, start_message1 = result['toto']
    assert puller1_cls == PullerActor
    assert start_message1.name == 'toto'

    db = start_message1.database

    assert isinstance(db, MongoDB)
    assert db.uri == 'titi'
    assert db.db_name == 'tata'
    assert db.collection_name == 'tutu'

    assert 'titi' in result
    puller2_cls, start_message2 = result['titi']
    assert puller2_cls == PullerActor
    assert start_message2.name == 'titi'

    db = start_message2.database

    assert isinstance(db, MongoDB)
    assert db.uri == 'titi'
    assert db.db_name == 'tata'
    assert db.collection_name == 'huhu'


#########################
# DBActorGenerator Test #
#########################
def test_remove_model_factory_that_does_not_exist_on_a_DBActorGenerator_must_raise_ModelNameDoesNotExist():
    generator = DBActorGenerator('input')

    with pytest.raises(ModelNameDoesNotExist):
        generator.remove_model_factory('model')


def test_remove_model_factory_that_does_not_exist_on_a_DBActorGenerator_must_raise_ModelNameDoesNotExist():
    generator = DBActorGenerator('input')

    with pytest.raises(ModelNameDoesNotExist):
        generator.remove_model_factory('model')


def test_remove_model_factory_that_does_not_exist_on_a_DBActorGenerator_must_raise_ModelNameDoesNotExist():
    generator = DBActorGenerator('input')

    with pytest.raises(ModelNameDoesNotExist):
        generator.remove_model_factory('model')

@patch('sys.exit', side_effect=SysExitException())
def test_remove_HWPCReport_model_and_generate_puller_from_a_config_with_hwpc_report_model_must_call_sys_exit_(mocked_sys_exit):
    args = {'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi',
                                                                   'db': 'tata', 'collection': 'tutu'}}}
    generator = PullerGenerator(None, [])
    generator.remove_model_factory('HWPCReport')
    with pytest.raises(SysExitException):
        result = generator.generate(args)


@patch('sys.exit', side_effect=SysExitException())
def test_remove_mongodb_factory_and_generate_puller_from_a_config_with_mongodb_input_must_call_sys_exit_(mocked_sys_exit):
    args = {'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi',
                                                                'db': 'tata', 'collection': 'tutu'}}}
    generator = PullerGenerator(None, [])
    generator.remove_db_factory('mongodb')
    with pytest.raises(SysExitException):
        result = generator.generate(args)
