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

pytest.importorskip('powerapi.processor.pre.openstack.monitor_agent')

from openstack.exceptions import SDKException
from openstack.compute.v2.server import Server

from powerapi.processor.pre.openstack.metadata_cache_manager import ServerMetadata
from powerapi.processor.pre.openstack.monitor_agent import OpenStackMonitorAgent


@pytest.fixture
def initialized_monitor_agent(initialized_metadata_cache_manager):
    """
    Returns an initialized OpenStack monitor agent.
    """
    return OpenStackMonitorAgent(initialized_metadata_cache_manager, poll_interval=0.01)


def make_server(server_id, server_name, host, instance_name, metadata) -> Server:
    """
    Generate a fake OpenStack server object.
    """
    server = Mock()
    server.id = server_id
    server.name = server_name
    server.host = host
    server.instance_name = instance_name
    server.metadata = metadata
    return server


def test_build_metadata_cache_entry_from_server(initialized_monitor_agent):
    """
    Test building a metadata cache entry from an OpenStack server object.
    """
    server = make_server('server-id', 'server-name', 'compute-1', 'instance-00000001', {'app': 'pytest'})

    metadata = initialized_monitor_agent.build_metadata_cache_entry_from_server(server)

    assert metadata == ServerMetadata('server-id', 'server-name', 'compute-1', 'instance-00000001', {'app': 'pytest'})


def test_fetch_servers_metadata(initialized_monitor_agent):
    """
    Test fetching OpenStack servers metadata.
    """
    server = make_server('server-id', 'server-name', 'compute-1', 'instance-00000001', {'app': 'pytest'})
    openstack_api = Mock()
    openstack_api.compute.servers.return_value = [server]

    metadata_entries = initialized_monitor_agent.fetch_servers_metadata(openstack_api)

    assert metadata_entries == [
        ServerMetadata('server-id', 'server-name', 'compute-1', 'instance-00000001', {'app': 'pytest'}),
    ]


def test_fetch_servers_metadata_returns_empty_list_on_sdk_exception(initialized_monitor_agent):
    """
    Test that OpenStack SDK errors return an empty server metadata list.
    """
    openstack_api = Mock()
    openstack_api.compute.servers.side_effect = SDKException('pytest')

    assert initialized_monitor_agent.fetch_servers_metadata(openstack_api) == []


def test_fetch_servers_metadata_returns_empty_list_on_missing_attribute(initialized_monitor_agent):
    """
    Test that missing OpenStack server attributes return an empty server metadata list.
    """
    server = make_server('server-id', 'server-name', 'compute-1', 'instance-00000001', {})
    del server.instance_name
    openstack_api = Mock()
    openstack_api.compute.servers.return_value = [server]

    assert initialized_monitor_agent.fetch_servers_metadata(openstack_api) == []
