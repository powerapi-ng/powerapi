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
from multiprocessing import active_children

import pytest


@pytest.fixture
def shutdown_system():
    """
    Shutdown the actor system, i.e., all actors are killed
    """
    yield None
    active = active_children()
    for child in active:
        child.kill()


@pytest.fixture
def power_timeline():
    """
    Timeline of procfs report for the tests
    """

    return [
        {
            "timestamp": "2021-09-14T12:37:37.168817",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:37.669237",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:38.170142",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:38.670338",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:39.171321",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:39.671572",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:40.172503",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:40.672693",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:41.173552",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:41.673815",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:42.174560",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:42.674690",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:43.175441",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:43.675743",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:44.176551",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:44.677307",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:45.178049",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:45.678310",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:46.179120",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:46.679308",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:47.180223",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:47.680468",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:48.181316",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:48.681683",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:49.182522",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:49.682731",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:50.183680",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:50.683812",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:51.184792",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:51.685027",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:52.185709",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:52.686065",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:53.186929",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:53.687190",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:54.188031",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:54.688674",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:55.189489",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:55.690299",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },
        {
            "timestamp": "2021-09-14T12:37:56.191124",
            "sensor": "formula_group",
            "target": "all",
            "power": 42,
        },

    ]
