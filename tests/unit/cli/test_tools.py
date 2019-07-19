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
    { 'verbose': True, 'stream': True, 'input': {'mongodb': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi', 'db': 'tata',
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
    args = {'verbose': True, 'stream': True, 'input': {'mongodb': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi',
                                                                   'db': 'tata', 'collection': 'tutu'}}}
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


def test_generate_puller_and_pusher_with_same_database():
    """
    generate mongodb puller and pusher from this config :
    {'verbose': True, 'stream': True, 'input': {'mongodb': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi', 'db': 'tata',
                                                'collection': 'tutu'}},
     'output': {'mongodb': {'model': 'hwpc_report', 'name': 'hoho', 'collection': 'tete'}}}
    as the database have the same uri and same database name, this value are not specified on the configuration of the output

    Test if :
      - puller and pusher database uri is titi
      - puller and pusher database db is tata
      - puller database collection is tutu
      - pusher database collection is tete

    """
    args = {'verbose': True, 'stream': True, 'input': {'mongodb': {'model': 'hwpc_report', 'name': 'toto', 'uri': 'titi',
                                                                   'db': 'tata', 'collection': 'tutu'}},
            'output': {'mongodb': {'model': 'hwpc_report', 'name': 'hoho', 'collection': 'tete'}}}

    puller_generator = PullerGenerator(None)
    result = puller_generator.generate(args)

    puller = result['toto']
    puller_db = puller.state.database

    pusher_generator = PusherGenerator()
    result = pusher_generator.generate(args)

    pusher = result['hoho']

    pusher_db = pusher.state.database

    assert pusher_db.uri == puller_db.uri
    assert pusher_db.db_name == puller_db.db_name
    assert pusher_db.collection_name == 'tete'
    assert puller_db.collection_name == 'tutu'
