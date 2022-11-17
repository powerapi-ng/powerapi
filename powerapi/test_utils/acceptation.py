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
from typing import Dict, Callable

from powerapi.actor import Supervisor
from powerapi.cli.generator import PusherGenerator, PullerGenerator
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.dispatcher import RouteTable, DispatcherActor
from powerapi.filter import Filter
from powerapi.formula import DummyFormulaActor
from powerapi.report import HWPCReport


def filter_rule(msg):
    return True


ROOT_DEPTH_LEVEL = 'ROOT'


def launch_simple_architecture(config: Dict, supervisor: Supervisor, hwpc_depth_level: str,
                               formula_class: Callable = DummyFormulaActor):
    """
    Launch a simple architecture with a pusher, a dispatcher et a puller.
    :param config: Architecture configuration
    :param supervisor: Supervisor to start and stop actors
    :param hwpc_depth_level: Depth level of the report ('ROOT' or 'SOCKET')
    :param formula_class: The class for create the formula
    """

    # Pusher
    pusher_generator = PusherGenerator()
    pusher_info = pusher_generator.generate(config)
    pusher = pusher_info['test_pusher']

    supervisor.launch_actor(actor=pusher, start_message=True)

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, hwpc_depth_level), primary=True))

    dispatcher = DispatcherActor(name='dispatcher',
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
    puller_generator = PullerGenerator(report_filter, [])
    puller_info = puller_generator.generate(config)
    puller = puller_info['test_puller']
    supervisor.launch_actor(actor=puller, start_message=True)
