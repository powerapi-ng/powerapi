# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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

from powerapi.report_model import PowerModel
from powerapi.report import PowerReport
from powerapi.cli.tools import PusherGenerator
from powerapi.utils import timestamp_to_datetime
from powerapi.backendsupervisor import BackendSupervisor

from tests.influx_utils import create_empty_db, delete_db, get_all_reports



INFLUX_URI = 'localhost'
INFLUX_PORT = 8086
INFLUX_DBNAME = 'acceptation_test'

SENSOR_NAME = 'sensor_test'
TARGET_NAME = 'system'

@pytest.fixture()
def influx_database():
    client = create_empty_db(INFLUX_URI, INFLUX_PORT)
    yield client
    delete_db(client, INFLUX_DBNAME)


@pytest.fixture
def supervisor():
    s = BackendSupervisor(False)
    yield s
    s.kill_actors()

@pytest.fixture
def power_report():
    return PowerReport(timestamp_to_datetime(1), SENSOR_NAME, TARGET_NAME, 1, 0.11, {"metadata1": "azerty", "metadata2": "qwerty"})





def test_generate_pusher_with_new_PowerReport_model_and_send_it_powerReport_must_store_PowerReport_with_right_tag(influx_database, supervisor, power_report):
    """
    Create a PusherGenerator that generate pusher with a PowerReportModel that keep formula_name metadata in PowerReport
    Generate a pusher connected to an influxDB
    send a powerReport with formula_name metadata to the pusher
    test if stored data was tag with formula_name
    """

    config = {'verbose': True, 'stream': False,
              'output': {'influxdb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': INFLUX_URI, 'port': INFLUX_PORT,
                                                      'db': INFLUX_DBNAME}}}}

    class PowerModelWithFormulaName(PowerModel):

        def _influxdb_keept_metadata(self):
            return PowerModel._influxdb_keept_metadata(self) + ('formula_name',)

    generator = PusherGenerator()
    generator.remove_model_factory('PowerReport')
    generator.add_model_factory('PowerReport', PowerModelWithFormulaName())

    actors = generator.generate(config)
    pusher = actors['test_pusher']
    supervisor.launch_actor(pusher)

    pusher.send_data(power_report)

    supervisor.kill_actors(soft=True)

    influx_database.switch_database(INFLUX_DBNAME)
    reports = list(influx_database.query('SELECT * FROM "power_consumption"'))

    assert len(reports[0]) == 1
    assert 'socket' in  reports[0][0]
    assert reports[0][0]['socket'] == '1'
