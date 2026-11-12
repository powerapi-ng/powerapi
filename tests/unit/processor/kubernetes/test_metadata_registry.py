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


def test_set_and_get_metadata(metadata_registry):
    """
    Metadata can be retrieved using its container ID.
    """
    container_id = 'e6eb9dd88e7189933861634cc9626b3a85a1f6425989caa51094df34c34c2787'
    metadata = {'k8s_pod_name': 'powerapi-pytest'}

    metadata_registry.set_metadata(container_id, metadata)

    assert metadata_registry.get_metadata(container_id) == metadata


def test_set_metadata_replaces_existing_entry(metadata_registry):
    """
    Setting metadata twice replaces the previous entry.
    """
    container_id = '35d31dfb0b83cf9d6c689711d9ab6f4667f6784107df3783a3333492cdbcbce2'
    metadata_registry.set_metadata(container_id, {'version': 'old'})

    metadata_registry.set_metadata(container_id, {'version': 'new'})

    assert metadata_registry.get_metadata(container_id) == {'version': 'new'}


def test_get_metadata_returns_none_for_unknown_container(metadata_registry):
    """
    An unknown container ID has no associated metadata.
    """
    container_id = '0000000000000000000000000000000000000000000000000000000000000000'

    assert metadata_registry.get_metadata(container_id) is None
