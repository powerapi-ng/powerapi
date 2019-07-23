"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import pytest
import sys

from mock import Mock

from powerapi.cli.tools import PullerGenerator, PusherGenerator
from powerapi.puller import PullerActor
from powerapi.database import MongoDB

####################
# PULLER GENERATOR #
####################
def test_no_input_specified():
    """
    generate puller from an empty config dict

    Test if the generate_puller function call sys.exit
    """
    args = {}
    sys.exit = Mock()
    sys.exit.side_effect = Exception()

    generator = PullerGenerator(None)

    with pytest.raises(Exception):
        generator.generate(args)

    assert sys.exit.called


def test_generate_puller_from_simple_config():
    """
    generate mongodb puller from this config :
    { 'verbose': True, 'stream': True, 'input': {'mongodb': {'toto': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'tutu'}}}}

    Test if :
      - function return a dict containing one actor, its key is 'toto'
      - puller type is PullerActor
      - puller name is toto
      - puller database type is MongoDB
      - database uri is titi
      - database db is tata
      - database collection is tutu

    """
    args = {'verbose': True, 'stream': True, 'input': {'mongodb': {'toto': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi',
                                                                   'db': 'tata', 'collection': 'tutu'}}}}
    generator = PullerGenerator(None)
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
    { 'verbose': True, 'stream': True, 'input': {'mongodb': {'toto': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'tutu'},
                                                             'titi': {'model': 'hwpc_report', 'name': 'titi', 'uri': 'titi', 'db': 'tata',
                                             'collection': 'huhu'}}}}

    Test if :
      - function return a dict containing two actor, their key are 'toto' and 'titi'
      - pullers type are PullerActor
      - pullers name are toto and titi
      - pullers database type are MongoDB
      - databases uri are titi
      - databases db are tata
      - databases collection are tutu and huhu

    """
    args =     { 'verbose': True, 'stream': True, 'input': {'mongodb': {'toto': {'model': 'hwpc_report', 'name': 'toto',
                                                                                 'uri': 'titi', 'db': 'tata', 'collection': 'tutu'},
                                                                        'titi': {'model': 'hwpc_report', 'name': 'titi',
                                                                                 'uri': 'titi', 'db': 'tata', 'collection': 'huhu'}}}}
    generator = PullerGenerator(None)
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


def test_generate_puller_from_with_default_config_database():
    """
    generate mongodb puller and pusher from this config :
    {'verbose': True, 'stream': True, 'input': {'mongodb_base_config': {'toto': {'model': 'hwpc_report', 'name': 'toto',
                                                'collection': 'tutu'}}},
     'db_config': {'mongodb_base_config': {'type' : 'mongodb', 'model': 'hwpc_report', 'name': 'hoho', 'uri': 'titi',
                                           'db': 'tata'}}}

    the generator must use the mongodb_base_config to generate the puller

    Test if :
      - puller database uri is titi
      - puller database db is tata
      - puller database collection is tutu

    """
    args = {'verbose': True,
            'stream': True,
            'input': {
                'mongodb': {
                    'toto': {
                        'default': 'mongodb_base_config',
                        'model': 'hwpc_report',
                        'config': 'mongodb_base_config',
                        'name': 'toto',
                        'collection': 'tutu'}}},
            'default_db_config': {
                'mongodb_base_config': {
                    'type': 'mongodb',
                    'uri': 'titi',
                    'db': 'tata'}}}

    generator = PullerGenerator(None)
    result = generator.generate(args)

    puller = result['toto']
    puller_db = puller.state.database

    assert puller_db.uri == 'titi'
    assert puller_db.db_name == 'tata'
    assert puller_db.collection_name == 'tutu'
