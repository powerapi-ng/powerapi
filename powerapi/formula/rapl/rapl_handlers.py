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
from math import ldexp

from powerapi.handler import Handler
from powerapi.report import PowerReport

RAPL_KEY = 'rapl'
RAPL_PREFIX = 'RAPL_'


class ReportHandler(Handler):
    """
    Handler behaviour for HWPC Reports
    """

    def _estimate(self, timestamp, target, counter):
        """
        Generate a power report using the given parameters.
        :param timestamp: Timestamp of the measurements
        :param target: Target name
        :param counter: Event counter
        :return: Power report filled with the given parameters
        """

        metadata = {
            'scope': self.state.config.scope.value,
            'socket': self.state.socket,
        }

        power = ldexp(counter, -32)

        report = PowerReport(timestamp, self.state.sensor, target, power, metadata)

        return report

    def handle(self, msg):
        """
         Process a HWPC report and send the result(s) to a pusher actor.
         :param msg: Received message
         """
        self.state.actor.logger.debug('received message ' + str(msg))
        if RAPL_KEY not in msg.groups:
            return

        reports = []
        for socket, socket_report in msg.groups[RAPL_KEY].items():
            for events_counter in socket_report.values():
                for event, counter in events_counter.items():
                    if event.startswith(RAPL_PREFIX):
                        reports.append(self._estimate(msg.timestamp, socket,
                                                      counter))

        for _, actor_pusher in self.state.pushers.items():
            for result in reports:
                actor_pusher.send_data(result)
