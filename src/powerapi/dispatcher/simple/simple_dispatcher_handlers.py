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
from powerapi.actor import State
from powerapi.handler import StartHandler, PoisonPillMessageHandler, Handler
from powerapi.message import StartMessage
from powerapi.exception import UnknownMessageTypeException
from powerapi.report import Report


class SimpleDispatcherStartHandler(StartHandler):
    """
    Initialize the formula associated to the dispatcher
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state)

    def initialization(self):
        self.state.formula.start()
        self.state.formula.connect_control()
        self.state.formula.connect_data()
        self.state.formula.send_control(StartMessage('system'))
        _ = self.state.formula.receive_control(2000)


class SimpleDispatcherPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    Simple Handler for PoisonPillMessage
    """
    def teardown(self, soft=False):
        if self.state.formula.is_alive():
            self.state.formula.terminate()
        self.state.formula.socket_interface.close()


class SimpleDispatcherReportHandler(Handler):
    """
    Transfer the reports to the formula
    """

    def __init__(self, state: State):
        Handler.__init__(self, state)

    def handle(self, msg: Report):
        """
        Transfers the report to the formula
        """
        self.state.actor.logger.debug('received ' + str(msg))
        if isinstance(msg, Report):
            self.state.actor.logger.debug('send ' + str(msg) + ' to ' + self.state.formula_name)
            self.state.formula.send_data(msg)
        else:
            raise UnknownMessageTypeException()
