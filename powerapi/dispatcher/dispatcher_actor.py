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

import logging
from powerapi.actor import Actor, SocketInterface
from powerapi.handler import PoisonPillMessageHandler
from powerapi.report import Report
from powerapi.message import PoisonPillMessage, StartMessage
from powerapi.dispatcher import StartHandler, DispatcherState
from powerapi.dispatcher import FormulaDispatcherReportHandler


class NoPrimaryDispatchRuleRuleException(Exception):
    """
    Exception raised when user want to get the primary dispatch_rule rule on a
    formula dispatcher that doesn't have one
    """


class DispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self, name, formula_init_function, route_table,
                 level_logger=logging.WARNING, timeout=None):
        """
        :param str name: Actor name
        :param func formula_init_function: Function for creating Formula
        :param route_table: initialized route table of the DispatcherActor
        :type route_table: powerapi.dispatcher.state.RouteTable
        :param int level_logger: Define the level of the logger
        :param bool timeout: Define the time in millisecond to wait for a
                             message before run timeout_handler
        """
        Actor.__init__(self, name, level_logger, timeout)

        # (func): Function for creating Formula
        self.formula_init_function = formula_init_function

        # (powerapi.DispatcherState): Actor state
        self.state = DispatcherState(self, self._create_factory(), route_table)

    def setup(self):
        """
        Check if there is a primary group by rule. Set define
        StartMessage, PoisonPillMessage and Report handlers
        """
        Actor.setup(self)
        if self.state.route_table.primary_dispatch_rule is None:
            raise NoPrimaryDispatchRuleRuleException()

        self.add_handler(Report, FormulaDispatcherReportHandler(self.state))
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler(self.state))
        self.add_handler(StartMessage, StartHandler(self.state))

    def teardown(self):
        """
        Override from Actor.

        Kill each formula before terminate
        """
        self.state.supervisor.kill_actors(by_data=True)

    def _create_factory(self):
        """
        Create the full Formula Factory

        :return: Formula Factory
        :rtype: func(formula_id) -> Formula
        """
        formula_init_function = self.formula_init_function

        def factory(formula_id):
            formula = formula_init_function(str((self.name,) + formula_id),
                                            self.logger.getEffectiveLevel())
            self.state.supervisor.launch_actor(formula, start_message=False)
            return formula

        return factory
