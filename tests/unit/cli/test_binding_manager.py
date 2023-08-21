# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
# All rights reserved.
import pytest

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

from powerapi.cli.binding_manager import ProcessorBindingManager, INPUT_GROUP, OUTPUT_GROUP, PROCESSOR_GROUP, \
    BINDING_GROUP
from powerapi.dispatcher import DispatcherActor
from powerapi.exception import PowerAPIException, UnsupportedActorTypeException, BadInputData
from powerapi.processor.processor_actor import ProcessorActor


def check_default_processor_binding_manager_default_actors_content(processor_manager: ProcessorBindingManager):
    """
    Check the default size for actors dictionary of the manager
    :param ProcessorBindingManager processor_manager: Binding manager to check the size
    """
    assert len(processor_manager.actors) == 3
    assert len(processor_manager.actors[INPUT_GROUP]) == 0
    assert len(processor_manager.actors[OUTPUT_GROUP]) == 0
    assert len(processor_manager.actors[PROCESSOR_GROUP]) == 0


def test_create_processor_binding_manager_with_actors(processor_binding_actors_and_dictionary):
    """
    Test that a ProcessorBindingManager is correctly created when an actor dictionary is provided
    """
    actors = {}

    for current_actors in processor_binding_actors_and_dictionary[0]:
        actors.update(current_actors)
    binding_manager = ProcessorBindingManager(actors=actors)

    assert binding_manager.actors == processor_binding_actors_and_dictionary[1]


def test_create_processor_binding_manager_without_actors():
    """
    Test that a ProcessorBindingManager is correctly created without a dictionary
    """
    binding_manager = ProcessorBindingManager(actors=None)

    check_default_processor_binding_manager_default_actors_content(processor_manager=binding_manager)


def test_create_processor_binding_manager_raise_exception_with_wrong_actor_type(dispatcher_actor_in_dictionary):
    """
    Test that a ProcessorBindingManager is correctly created without a dictionary
    """
    with pytest.raises(UnsupportedActorTypeException):
        _ = ProcessorBindingManager(actors=dispatcher_actor_in_dictionary)


def test_add_actors(processor_binding_actors_and_dictionary):
    """
    Test that a dictionary is correctly generated according to a list of actors
    """
    binding_manager = ProcessorBindingManager(actors=[])

    check_default_processor_binding_manager_default_actors_content(processor_manager=binding_manager)

    for actors in processor_binding_actors_and_dictionary[0]:
        binding_manager.add_actors(actors)

    assert binding_manager.actors == processor_binding_actors_and_dictionary[1]


def test_add_actors_raise_exception_with_wrong_actor_type(dispatcher_actor_in_dictionary):
    """
    Test that a dictionary is correctly generated according to a list of actors
    """
    binding_manager = ProcessorBindingManager(actors=[])

    check_default_processor_binding_manager_default_actors_content(processor_manager=binding_manager)

    with pytest.raises(UnsupportedActorTypeException):
        binding_manager.add_actors(dispatcher_actor_in_dictionary)

    check_default_processor_binding_manager_default_actors_content(processor_manager=binding_manager)


def test_process_bindings_for_processor(puller_to_processor_binding_configuration,
                                        processor_binding_actors_and_dictionary):
    """
    Test that the bindings between a puller and a processor are correctly created
    """
    actors = {}

    for current_actors in processor_binding_actors_and_dictionary[0]:
        actors.update(current_actors)

    binding_manager = ProcessorBindingManager(actors=actors)

    assert len(actors['one_puller'].state.report_filter.filters) == 1
    assert isinstance(actors['one_puller'].state.report_filter.filters[0][1], DispatcherActor)

    binding_manager.process_bindings(bindings=puller_to_processor_binding_configuration[BINDING_GROUP])

    assert len(actors['one_puller'].state.report_filter.filters) == 1
    assert isinstance(actors['one_puller'].state.report_filter.filters[0][1], ProcessorActor)
    assert actors['one_puller'].state.report_filter.filters[0][1] == actors['my_processor']


def test_process_bindings_for_processor_raise_exception_with_wrong_binding_types(
        pusher_to_processor_wrong_binding_configuration,
        processor_binding_manager):
    """
    Test that an exception is raised with a wrong type for the from actor in a binding
    """

    with pytest.raises(BadInputData):
        processor_binding_manager.process_bindings(
            bindings=pusher_to_processor_wrong_binding_configuration[BINDING_GROUP])


def test_process_bindings_for_processor_raisse_exception_with_non_existent_puller(
        not_existent_puller_to_processor_configuration,
        processor_binding_manager):
    """
    Test that an exception is raised with a non-existent puller
    """

    with pytest.raises(BadInputData):
        processor_binding_manager.process_bindings(
            bindings=not_existent_puller_to_processor_configuration[BINDING_GROUP])
