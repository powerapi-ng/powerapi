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
from typing import Dict, Any

from powerapi.actor import Actor
from powerapi.formula.formula_actor import FormulaActor, FormulaState
from powerapi.pusher import PusherActor


class AbstractCpuDramFormulaState(FormulaState):
    """
    Formula values with configurable sleeping time for dummy formula
    """

    def __init__(self, actor: Actor, pushers: Dict[str, Actor], metadata: Dict[str, Any], socket: str, core: str):
        FormulaState.__init__(self, actor, pushers, metadata)
        self.socket = socket
        self.core = core


class AbstractCpuDramFormula(FormulaActor):
    """
    Formula that handle CPU or DRAM related data
    It can be launched to handle data from a specific part of a cpu (whole cpu, a socket or a core)
    """

    def __init__(self, name, pushers: Dict[str, PusherActor], socket: str, core: str, level_logger=logging.WARNING,
                 timeout=None):
        FormulaActor.__init__(self, name, pushers, level_logger, timeout)
        self.state = AbstractCpuDramFormulaState(self, pushers, self.formula_metadata, socket, core)
