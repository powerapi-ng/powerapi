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

from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture(name='pods_list')
def basic_pods_list():
    """
    Return a list of three pods
    """
    return ['pod1', 'pod2', 'pod3']


class FakeMetadata:
    """
    Fake metadata class related to an event
    """

    def __init__(self, name: str, namespace: str, labels: dict[str, str]):
        self.name = name
        self.namespace = namespace
        self.labels = labels


class FakeContainerStatus:
    """
    Fake container status infos related to an event
    """

    def __init__(self, container_id: str):
        self.container_id = container_id


class FakeStatus:
    """
    Fake status infos related to an event
    """

    def __init__(self, container_statuses: list):
        self.container_statuses = container_statuses


class FakePod:
    """
    Fake pod class related to an event
    """

    def __init__(self, metadata: FakeMetadata, status: FakeStatus):
        self.metadata = metadata
        self.status = status


@pytest.fixture(name='events_list_k8s')
def basic_events_list_k8s():
    """
    Return a list of three events
    """
    return [
        {
            'type': 'ADDED',
            'object': FakePod(
                FakeMetadata('o1', 's1', {'l1': 'l1label', 'l2': 'l2label'}),
                FakeStatus([
                    FakeContainerStatus('test://s1c1'),
                    FakeContainerStatus('test://s1c2'),
                    FakeContainerStatus('test://s1c3')
                ])
            )
        },
        {
            'type': 'MODIFIED',
            'object': FakePod(
                FakeMetadata('o2', 's2', {'l1': 'l1label', 'l2': 'l2label'}),
                FakeStatus([
                    FakeContainerStatus('test://s2c1'),
                    FakeContainerStatus('test://s2c2'),
                    FakeContainerStatus('test://s2c3')
                ])
            )
        },
        {
            'type': 'DELETED',
            'object': FakePod(
                FakeMetadata('o3', 's3', {'l1': 'l1label', 'l2': 'l2label'}),
                FakeStatus([])
            )
        }
    ]


@pytest.fixture(name='unknown_events_list_k8s')
def basic_unknown_events_list_k8s(events_list_k8s):
    """
    Modify and return an event list with unknown events types
    """
    event_count = len(events_list_k8s)

    for event_indice in range(event_count):
        events_list_k8s[event_indice]['type'] = 'Unknown_' + str(event_indice)

    return events_list_k8s


class MockedWatch(Mock):
    """
    Mocked class for simulating the Watch class from K8s API
    """

    def __init__(self, events):
        Mock.__init__(self)
        self.events = events
        self.args = None
        self.timeout_seconds = 0
        self.func = None

    def stream(self, func: Any, timeout_seconds: int, *args):
        """
        Return the list of events related to the MockedWatch
        """
        self.args = args
        self.timeout_seconds = timeout_seconds
        self.func = func
        return self.events


@pytest.fixture
def mocked_watch_initialized(events_list_k8s):
    """
    Return a MockedWatch with the event list
    """
    return MockedWatch(events_list_k8s)


@pytest.fixture
def mocked_watch_initialized_unknown_events(unknown_events_list_k8s):
    """
    Return a MockedWatch with a list of unknown events
    """
    return MockedWatch(unknown_events_list_k8s)
