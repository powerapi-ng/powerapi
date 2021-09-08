# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import pytest

from thespian.actors import ActorExitRequest

from powerapi.report import PowerReport
from powerapi.cli.tools import PusherGenerator
from powerapi.utils import timestamp_to_datetime
from powerapi.test_utils.actor import system
from powerapi.test_utils.db.influx import INFLUX_URI, INFLUX_PORT, INFLUX_DBNAME, influx_database


SENSOR_NAME = 'sensor_test'
TARGET_NAME = 'system'


@pytest.fixture
def power_report():
    return PowerReport(timestamp_to_datetime(1), SENSOR_NAME, TARGET_NAME, 0.11, {'socket': 1, 'metadata1': 'azerty', 'metadata2': 'qwerty'})

@pytest.fixture
def influxdb_content():
    return []



def test_generate_pusher_with_socket_tags_and_send_it_a_powerReport_must_store_PowerReport_with_right_tag(system, influx_database, power_report):
    """
    Create a PusherGenerator that generate pusher with a PowerReportModel that keep formula_name metadata in PowerReport
    Generate a pusher connected to an influxDB
    send a powerReport with formula_name metadata to the pusher
    test if stored data have tag with formula_name
    """

    config = {'verbose': True,
              'stream': False,
              'output': {'test_pusher': {'type': 'influxdb',
                                         'tags': 'socket',
                                         'model': 'PowerReport',
                                         'name': 'test_pusher',
                                         'uri': INFLUX_URI,
                                         'port': INFLUX_PORT,
                                         'db': INFLUX_DBNAME}}
              }


    generator = PusherGenerator()
    generator.remove_model_factory('PowerReport')
    generator.add_model_factory('PowerReport', PowerReport)

    actors = generator.generate(config)
    pusher_cls, pusher_start_message = actors['test_pusher']

    pusher = system.createActor(pusher_cls)
    system.ask(pusher, pusher_start_message)
    system.tell(pusher, power_report)
    import time
    time.sleep(0.1)
    system.tell(pusher, ActorExitRequest())
    influx_database.switch_database(INFLUX_DBNAME)
    reports = list(influx_database.query('SELECT * FROM "power_consumption"').get_points(tags={'socket': '1'}))
    assert len(reports) == 1
