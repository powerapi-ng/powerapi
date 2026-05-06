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

from powerapi.processor.pre.openstack.metadata_cache_manager import ServerMetadata


def test_update_and_get_server_metadata(initialized_metadata_cache_manager):
    """
    Test storing and retrieving OpenStack server metadata.
    """
    metadata = ServerMetadata('server-id', 'server-name', 'compute-1', 'instance-00000001', {'app': 'pytest'})

    initialized_metadata_cache_manager.update_server_metadata(metadata)

    assert initialized_metadata_cache_manager.get_server_metadata('compute-1', 'instance-00000001') == metadata


def test_update_server_metadata_uses_host_and_instance_name(initialized_metadata_cache_manager):
    """
    Test that OpenStack server metadata is indexed by host and instance name.
    """
    first_metadata = ServerMetadata('server-id-a', 'server-name-a', 'compute-1', 'instance-00000001', {})
    second_metadata = ServerMetadata('server-id-b', 'server-name-b', 'compute-1', 'instance-00000002', {'app': 'pytest'})

    initialized_metadata_cache_manager.update_server_metadata(first_metadata)
    initialized_metadata_cache_manager.update_server_metadata(second_metadata)

    assert initialized_metadata_cache_manager.get_server_metadata('compute-1', 'instance-00000001') == first_metadata
    assert initialized_metadata_cache_manager.get_server_metadata('compute-1', 'instance-00000002') == second_metadata


def test_clear_metadata_cache(initialized_metadata_cache_manager):
    """
    Test clearing the OpenStack metadata cache.
    """
    metadata = ServerMetadata('server-id', 'server-name', 'compute-1', 'instance-00000001', {})
    initialized_metadata_cache_manager.update_server_metadata(metadata)

    initialized_metadata_cache_manager.clear_metadata_cache()

    assert initialized_metadata_cache_manager.get_server_metadata('compute-1', 'instance-00000001') is None
