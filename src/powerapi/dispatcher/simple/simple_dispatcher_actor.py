# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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
import logging
from typing import Callable, Literal

from powerapi.actor import Actor, State
from powerapi.dispatcher import RouteTable
from powerapi.dispatcher.simple.simple_dispatcher_handlers import SimpleDispatcherStartHandler, \
    SimpleDispatcherPoisonPillMessageHandler, SimpleDispatcherReportHandler
from powerapi.message import StartMessage, PoisonPillMessage
from powerapi.report import Report


class SimpleDispatcherState(State):
    """
        Simple Disparcher Actor State

        Contains in addition to State values :
          - the number of reports to send
          - the report type to send
          - the report filter
        """

    def __init__(self, actor, formula_name: str, formula_init_function: Callable, pushers: [], route_table: RouteTable):
        """
        :param Actor actor: The actor related to the state
        :param Callable formula_init_function: Function for creating the formula related to the dispatcher
        :param RouteTable route_table: the route table associating report type with a rule
        """
        State.__init__(self, actor)
        self.formula_init_function = formula_init_function
        self.pushers = pushers
        self.route_table = route_table
        self.formula_name = formula_name
        self.formula = None


class SimpleDispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self, name: str, formula_init_function: Callable, pushers: [], route_table: RouteTable,
                 level_logger: Literal = logging.WARNING, timeout=None):
        Actor.__init__(self, name, level_logger, timeout)
        self.state = SimpleDispatcherState(self, 'simple-formula', formula_init_function, pushers, route_table)

    def setup(self):
        """
        Define StartMessage, PoisonPillMessage and Report handlers
        """
        Actor.setup(self)
        self._create_formula()
        self.add_handler(PoisonPillMessage, SimpleDispatcherPoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, SimpleDispatcherStartHandler(self.state))
        self.add_handler(Report, SimpleDispatcherReportHandler(self.state))

    def _create_formula(self):
        self.state.formula = self.state.formula_init_function(self.state.formula_name, self.state.pushers,
                                                              self.logger.getEffectiveLevel())
        self.logger.info('create formula ' + self.state.formula_name)
