# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
#
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

from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.formula.rapl.rapl_formula_actor import RAPLFormulaConfig


class RAPLDispatcherActor(DispatcherActor):
    """
    Dispatcher Actor for RAPL
    """
    def __init__(self, name: str, formula_init_function: Callable, pushers: [], route_table: RouteTable, device_id: str,
                 formula_config: RAPLFormulaConfig, level_logger: Literal = logging.WARNING, timeout=None):
        DispatcherActor.__init__(self, name=name, formula_init_function=formula_init_function, pushers=pushers,
                                 route_table=route_table, level_logger=level_logger, timeout=timeout,
                                 device_id=device_id)
        self.formula_config = formula_config

    def _create_factory(self, pushers: []):
        """
        Create the full Formula Factory

        :return: Formula Factory
        :rtype: func(formula_id) -> Formula
        """
        formula_init_function = self.formula_init_function

        def factory(formula_id):
            socket = None if len(formula_id) <= 1 else int(formula_id[1])
            core = None if len(formula_id) <= 2 else int(formula_id[2])
            formula = formula_init_function(name=str((self.name,) + formula_id), pushers=pushers,
                                            socket=socket, core=core, config=self.formula_config,
                                            sensor=self.device_id, level_logger=self.logger.level)
            self.state.supervisor.launch_actor(formula, start_message=False)
            return formula

        return factory
