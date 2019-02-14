# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
                 level_logger=logging.NOTSET, timeout=None):
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
        self.state = DispatcherState(Actor._initial_behaviour,
                                     SocketInterface(name, timeout),
                                     self._create_factory(), route_table)

    def setup(self):
        """
        Check if there is a primary group by rule. Set define
        StartMessage, PoisonPillMessage and Report handlers
        """
        Actor.setup(self)
        if self.state.route_table.primary_dispatch_rule_rule is None:
            raise NoPrimaryDispatchRuleRuleException()

        self.add_handler(Report, FormulaDispatcherReportHandler())
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())
        self.add_handler(StartMessage, StartHandler())

    def terminated_behaviour(self):
        """
        Override from Actor.

        Kill each formula before terminate
        """
        for name, formula in self.state.get_all_formula():
            formula.kill(by_data=True)
            formula.join()

    def _create_factory(self):
        """
        Create the full Formula Factory

        :return: Formula Factory
        :rtype: func(formula_id, context) -> Formula
        """
        # context = self.state.socket_interface.context
        formula_init_function = self.formula_init_function

        def factory(formula_id, context):
            formula = formula_init_function(str(formula_id),
                                            self.logger.getEffectiveLevel())
            formula.connect_data(context)
            formula.connect_control(context)
            return formula

        return factory
