#!/usr/bin/env python3

# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import datetime

from powerapi.report import ProcfsReport

SENSOR_NAME = 'sensor_test'
TARGET_NAME = 'target_test'


def gen_json_procfs_report(number_of_reports):
    """
    generate number_of_reports power report with json format
    each power report have the same sensor, target and power value (100W)
    only the timestamp is different.
    timestamp is generated from 01/01/1970 0:00.0 for the first report and is incremented by 1s for each returned report
    """
    reports = []
    for ts in range(number_of_reports):
        tmstp_tmp = str(datetime.datetime.fromtimestamp(ts))
        tmstp = tmstp_tmp[:tmstp_tmp.index(' ')] + 'T' + tmstp_tmp[tmstp_tmp.index(' ') + 1:] + '.0'
        reports.append(
            {
            "timestamp": tmstp,
            "sensor": "formula_group",
            "target": ["firefox_cgroup", "emacs_cgroup",
                       "zsh_cgroup", "mongo_cgroup"],
            "usage": {
                "firefox_cgroup": 8.36,
                "emacs_cgroup": 5.52,
                "zsh_cgroup": 0.01,
                "mongo_cgroup": 0.64,
            },
            "global_cpu_usage": 27.610000000000014,
            }
        )
    return reports
