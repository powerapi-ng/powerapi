# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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

from powerapi.processor.pre.k8s.metadata_cache_manager import ADDED_EVENT, MODIFIED_EVENT, DELETED_EVENT
from powerapi.processor.pre.k8s.metadata_cache_manager import K8sContainerMetadata


def _generate_metadata_cache_entry(container_id: str, counter: int = 0) -> K8sContainerMetadata:
    """
    Generate a K8sContainerMetadata object from the given parameters.
    """
    container_name = 'powerapi-test-container'
    namespace = 'powerapi-test-namespace'
    pod_name = 'powerapi-test-pod'
    pod_labels = {
        'app.kubernetes.io/name': 'powerapi-test-app',
        'app.kubernetes.io/instance': 'powerapi-test-app-abcxzy',
        'app.kubernetes.io/version': 'v1.0.0',
        'app.kubernetes.io/component': 'test',
        'app.kubernetes.io/part-of': 'powerapi-test',
        'helm.sh/chart': 'powerapi-test-1.0.0',
        'powerapi.org/test-counter': counter
    }
    return K8sContainerMetadata(container_id, container_name, namespace, pod_name, pod_labels)


def test_container_metadata_cache_with_added_event(initialized_metadata_cache_manager):
    """
    Test that an 'ADDED' event add the entry to the metadata cache.
    """
    container_id = 'e6eb9dd88e7189933861634cc9626b3a85a1f6425989caa51094df34c34c2787'
    entry = _generate_metadata_cache_entry(container_id)
    initialized_metadata_cache_manager.update_container_metadata(ADDED_EVENT, entry)

    assert initialized_metadata_cache_manager.get_container_metadata(container_id) == entry


def test_container_metadata_cache_with_updated_event(initialized_metadata_cache_manager):
    """
    Test that an 'MODIFIED' event update the entry in the metadata cache.
    """
    container_id = '35d31dfb0b83cf9d6c689711d9ab6f4667f6784107df3783a3333492cdbcbce2'

    first_entry = _generate_metadata_cache_entry(container_id, 0)
    initialized_metadata_cache_manager.update_container_metadata(ADDED_EVENT, first_entry)

    second_entry = _generate_metadata_cache_entry(container_id, 1)
    initialized_metadata_cache_manager.update_container_metadata(MODIFIED_EVENT, second_entry)

    assert initialized_metadata_cache_manager.get_container_metadata(container_id) == second_entry


def test_container_metadata_cache_with_deleted_event(initialized_metadata_cache_manager):
    """
    Test that an 'DELETED' event remove the entry from the metadata cache.
    """
    container_id = '885754eae01c1e4d5389677d6bab564381c12500324c8da9731ac74452740faa'
    entry = _generate_metadata_cache_entry(container_id)
    initialized_metadata_cache_manager.update_container_metadata(DELETED_EVENT, entry)

    assert initialized_metadata_cache_manager.get_container_metadata(container_id) is None


def test_container_metadata_cache_with_valid_container_id(initialized_metadata_cache_manager):
    """
    Test fetching a metadata cache entry with a valid container id.
    """
    container_id = '5375cd086e95601123cedbd0d1dc77058fb7d9890ae67aed0f551e032e1ebf87'

    entry = _generate_metadata_cache_entry(container_id)
    initialized_metadata_cache_manager.update_container_metadata(ADDED_EVENT, entry)

    fetched_entry = initialized_metadata_cache_manager.get_container_metadata(container_id)

    assert fetched_entry is not None
    assert fetched_entry == entry


def test_container_metadata_cache_with_unknown_container_id(initialized_metadata_cache_manager):
    """
    Test fetching a metadata cache entry with an unknown container id.
    """
    container_id = '0000000000000000000000000000000000000000000000000000000000000000'
    entry = initialized_metadata_cache_manager.get_container_metadata(container_id)

    assert entry is None


def test_container_metadata_cache_clear(initialized_metadata_cache_manager):
    """
    Test clearing the metadata cache.
    """
    container_id = '9c4b8e6491219cf5112bdc8c6aab02ff19ccc8870cda70f264a41add2dc57fbb'
    entry = _generate_metadata_cache_entry(container_id)
    initialized_metadata_cache_manager.update_container_metadata(ADDED_EVENT, entry)

    assert len(initialized_metadata_cache_manager.metadata_cache) == 1

    initialized_metadata_cache_manager.clear_metadata_cache()

    assert len(initialized_metadata_cache_manager.metadata_cache) == 0
