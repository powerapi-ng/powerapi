# Copyright (c) 2023, Inria
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

from multiprocessing import active_children

import pytest

from tests.utils.db.mongo import MONGO_URI, MONGO_DATABASE_NAME, MONGO_OUTPUT_COLLECTION_NAME


@pytest.fixture
def shutdown_system():
    """
    Shutdown the actor system, i.e., all actors are killed
    """
    yield None
    active = active_children()
    for child in active:
        child.kill()


@pytest.fixture()
def socket_info_config():
    """
    Return a configuration with socket as input and mongo as output
    """
    return {'verbose': True,
            'stream': False,
            'input': {'test_puller': {'type': 'socket',
                                      'port': 0,
                                      'model': 'HWPCReport'}},
            'output': {'test_pusher': {'type': 'mongodb',
                                       'uri': MONGO_URI,
                                       'db': MONGO_DATABASE_NAME,
                                       'model': 'PowerReport',
                                       'max_buffer_size': 0,
                                       'collection': MONGO_OUTPUT_COLLECTION_NAME}},
            }
