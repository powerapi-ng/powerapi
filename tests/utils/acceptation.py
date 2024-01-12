# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
import signal
import string
import sys
import time
from multiprocessing import Process
from typing import Dict, Callable

import pytest

from powerapi.actor import Supervisor
from powerapi.cli.generator import PusherGenerator, PullerGenerator
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.dispatcher import RouteTable, DispatcherActor
from powerapi.filter import Filter
from powerapi.report import HWPCReport
from tests.utils.db.csv import OUTPUT_PATH, FILES
from tests.utils.db.mongo import MONGO_URI, MONGO_DATABASE_NAME, MONGO_OUTPUT_COLLECTION_NAME, \
    MONGO_INPUT_COLLECTION_NAME
from tests.utils.libvirt import REGEXP
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets


def filter_rule(_):
    """
    Default filter rule
    """
    return True


ROOT_DEPTH_LEVEL = 'ROOT'
SOCKET_DEPTH_LEVEL = 'SOCKET'

BASIC_CONFIG = {'verbose': True,
                'stream': False,
                'output': {'test_pusher': {'type': 'mongodb',
                                           'model': 'PowerReport',
                                           'uri': MONGO_URI,
                                           'db': MONGO_DATABASE_NAME,
                                           'max_buffer_size': 0,
                                           'collection': MONGO_OUTPUT_COLLECTION_NAME}},
                'input': {'test_puller': {'type': 'mongodb',
                                          'model': 'HWPCReport',
                                          'uri': MONGO_URI,
                                          'db': MONGO_DATABASE_NAME,
                                          'collection': MONGO_INPUT_COLLECTION_NAME}}
                }

CSV_INPUT_OUTPUT_CONFIG = {'verbose': True,
                           'stream': False,
                           'output': {'test_pusher': {'type': 'csv',
                                                      'tags': 'socket',
                                                      'model': 'PowerReport',
                                                      'max_buffer_size': 0,
                                                      'directory': OUTPUT_PATH}},
                           'input': {'test_puller': {'type': 'csv',
                                                     'files': FILES,
                                                     'model': 'HWPCReport'}},
                           }

LIBVIRT_CONFIG = {'verbose': True,
                  'stream': False,
                  'input': {'test_puller': {'type': 'mongodb',
                                            'uri': MONGO_URI,
                                            'db': MONGO_DATABASE_NAME,
                                            'collection': MONGO_INPUT_COLLECTION_NAME,
                                            'model': 'HWPCReport',
                                            }},
                  'output': {'test_pusher': {'type': 'mongodb',
                                             'uri': MONGO_URI,
                                             'db': MONGO_DATABASE_NAME,
                                             'collection': MONGO_OUTPUT_COLLECTION_NAME,
                                             'model': 'PowerReport',
                                             'max_buffer_size': 0, }},
                  'report_modifier': {'libvirt_mapper': {'uri': '',
                                                         'domain_regexp': REGEXP}}
                  }

DISPATCHER_ACTOR_NAME = "dispatcher"


def get_basic_config_with_stream():
    """
    Return the basic config with actived stream
    """

    config_stream = BASIC_CONFIG
    config_stream['stream'] = True
    return config_stream


def launch_simple_architecture(config: Dict, supervisor: Supervisor, hwpc_depth_level: str,
                               formula_class: Callable):
    """
    Launch a simple architecture with a pusher, a dispatcher et a puller.
    :param config: Architecture configuration
    :param supervisor: Supervisor to start and stop actors
    :param hwpc_depth_level: Depth level of the report ('ROOT' or 'SOCKET')
    :param formula_class: The class for create the formula
    :param generate_report_modifier_list: Boolean indicating if a list of modifiers has to be generated
    """

    # Pusher
    pusher_generator = PusherGenerator()
    pusher_info = pusher_generator.generate(config)
    pusher = pusher_info['test_pusher']

    supervisor.launch_actor(actor=pusher, start_message=True)

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, hwpc_depth_level), primary=True))

    dispatcher = DispatcherActor(name=DISPATCHER_ACTOR_NAME,
                                 formula_init_function=lambda name, pushers: formula_class(name=name,
                                                                                           pushers=pushers,
                                                                                           socket=0,
                                                                                           core=0),
                                 route_table=route_table,
                                 pushers={'test_pusher': pusher})

    supervisor.launch_actor(actor=dispatcher, start_message=True)

    # Puller
    report_filter = Filter()
    report_filter.filter(filter_rule, dispatcher)

    puller_generator = PullerGenerator(report_filter)
    puller_info = puller_generator.generate(config)
    puller = puller_info['test_puller']
    supervisor.launch_actor(actor=puller, start_message=True)


def get_actor_by_name(actor_name: str, actors: []):
    """
        Return an actor with the given name inside a provided list of actors

        :param actor_name: The name of the actor for looking for
        :param actors: The list of actors to execute the search
    """
    for actor in actors:
        if actor.name == actor_name:
            return actor

    return None


@pytest.fixture
def mongodb_content():
    """
        Get reports from a file for testing purposes
    """
    return extract_rapl_reports_with_2_sockets(10)


class MainProcess(Process):
    """
    Process that run the global architecture and crash the dispatcher
    """

    def __init__(self, name: string, formula_class: str, sleep_time: int):
        Process.__init__(self, name=name)
        self.formula_class = formula_class
        self.sleep_time = sleep_time
        self.supervisor = Supervisor()

    def run(self):
        # Setup signal handler
        def term_handler(_, __):
            # Kill puller, dispatcher and pusher
            self.supervisor.kill_actors()
            sys.exit(0)

        signal.signal(signal.SIGTERM, term_handler)
        signal.signal(signal.SIGINT, term_handler)

        launch_simple_architecture(config=BASIC_CONFIG, supervisor=self.supervisor,
                                   hwpc_depth_level=ROOT_DEPTH_LEVEL, formula_class=self.formula_class)

        time.sleep(self.sleep_time)
