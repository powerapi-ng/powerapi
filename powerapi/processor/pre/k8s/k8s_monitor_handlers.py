# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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
from threading import Thread

from powerapi.actor import State
from powerapi.handler import StartHandler, PoisonPillMessageHandler


class K8sMonitorAgentStartMessageHandler(StartHandler):
    """
    Start the K8sMonitorAgent
    """

    def __init__(self, state: State):
        StartHandler.__init__(self, state=state)

    def initialization(self):
        self.state.active_monitoring = True
        self.state.listener_agent.connect_data()
        monitoring_thread = Thread(target=self.state.actor.query_k8s)
        monitoring_thread.start()
        self.state.monitor_thread = monitoring_thread


class K8sMonitorAgentPoisonPillMessageHandler(PoisonPillMessageHandler):
    """
    Stop the K8sMonitorAgent
    """

    def __init__(self, state: State):
        PoisonPillMessageHandler.__init__(self, state=state)

    def teardown(self, soft=False):
        self.state.actor.logger.debug('teardown monitor')
        self.state.active_monitoring = False
        self.state.monitor_thread.join(10)