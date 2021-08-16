# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from powerapi.cli.tools import PullerGenerator, PusherGenerator, DBActorGenerator
from powerapi.cli.tools import ModelNameDoesNotExist, DatabaseNameDoesNotExist
from powerapi.puller import PullerActor
from powerapi.database import MongoDB

####################
# PULLER GENERATOR #
####################

class SysExitException(Exception):
    pass


@patch('sys.exit', side_effect=SysExitException())
def test_no_input_specified(mocked_sys_exit):
    """
    generate puller from an empty config dict

    Test if the generate_puller function call sys.exit
    """
    args = {}
    # sys.exit = Mock()
    # sys.exit.side_effect = Exception()

    generator = PullerGenerator(None, [])

    with pytest.raises(SysExitException):
        generator.generate(args)

    # assert sys.exit.called


def test_generate_puller_from_simple_config():
    """
    generate mongodb puller from this config :
    { 'verbose': True, 'stream': True, 'input': {'toto': {'model': 'HWPCReport', 'type': 'mongodb', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'tutu'}}}

    Test if :
      - function return a dict containing one actor, its key is 'toto'
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
    puller = result['toto']
    assert isinstance(puller, PullerActor)
    assert puller.name == 'toto'

    db = puller.state.database

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
    puller = result['toto']
    assert isinstance(puller, PullerActor)
    assert puller.name == 'toto'

    db = puller.state.database

    assert isinstance(db, MongoDB)
    assert db.uri == 'titi'
    assert db.db_name == 'tata'
    assert db.collection_name == 'tutu'

    assert 'titi' in result
    puller = result['titi']
    assert isinstance(puller, PullerActor)
    assert puller.name == 'titi'

    db = puller.state.database

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
