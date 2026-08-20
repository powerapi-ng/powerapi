# Copyright (c) 2026, Inria
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

from unittest.mock import Mock

import pytest

pytest.importorskip('openstack')

from openstack.compute.v2.server import Server

from powerapi.processor.pre.openstack.server_change_handler import (
    OpenStackServerChangeHandler,
)


def make_server(status: str = 'ACTIVE') -> Server:
    """
    Build an OpenStack server containing the attributes used by the change handler.
    """
    server = Mock(spec=Server)
    server.name = 'server-name'
    server.host = 'compute-1'
    server.instance_name = 'instance-00000001'
    server.status = status
    server.project_id = 'project-id'
    server.availability_zone = 'nova'
    server.metadata = {
        'environment': 'pytest',
        'ignored': 'ignored',
    }
    return server


def test_server_change_registers_selected_metadata(metadata_registry):
    """
    A server change should register only selected metadata.
    """
    handler = OpenStackServerChangeHandler(
        metadata_registry,
        {'environment': 'openstack_metadata_environment'},
    )
    server = make_server()

    handler.handle(server)

    assert metadata_registry.get_metadata(server.host, server.instance_name) == {
        'openstack_server_name': server.name,
        'openstack_project_id': server.project_id,
        'openstack_availability_zone': server.availability_zone,
        'openstack_metadata_environment': 'pytest',
    }


def test_deleted_server_change_retains_metadata(metadata_registry):
    """
    A deleted server change should leave existing metadata intact.
    """
    metadata = {'openstack_server_id': 'server-id'}
    metadata_registry.set_metadata('compute-1', 'instance-00000001', metadata)
    handler = OpenStackServerChangeHandler(metadata_registry, {})

    handler.handle(make_server(status='DELETED'))

    assert metadata_registry.get_metadata('compute-1', 'instance-00000001') == metadata
