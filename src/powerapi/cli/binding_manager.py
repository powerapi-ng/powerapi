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

from powerapi.exception import UnsupportedActorTypeException, UnexistingActorException, TargetActorAlreadyUsed
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor


class BindingManager:
    """
    Class for management the binding between actors during their creation process
    """

    def __init__(self, actors: dict | None = None, config: dict | None = None):
        """
        :param dict actors: Dictionary of actors to create the bindings. The name of the actor is the key
        """
        self.actors = {} if not actors else actors
        self.config = {} if not config else config

    def process_bindings(self):
        """
        Define bindings between self.actors according to the processors' targets.
        """
        raise NotImplementedError()


class ProcessorBindingManager(BindingManager):
    """
    Class for management of bindings between processor actors and others actors
    """

    def __init__(self, actors: dict | None, processors: dict | None, config: dict | None = None):
        """
        The ProcessorBindingManager defines bindings between actors and processors
        :param dict actors: Dictionary of actors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        :param dict processors: Dictionary of processors with structure {<processor1_key>:processor1,
        <processor2_key>:processor2...}
        """
        super().__init__(actors=actors, config=config)
        self.processors = {} if not processors else processors

    def _get_processor_target_names(self, processor_name: str) -> list[str]:
        """
        Return target actor names configured for the given processor.
        """
        pre_processor_config = self.config.get('pre-processor', {}).get(processor_name, {})
        puller_name = pre_processor_config.get('puller')
        return [] if puller_name is None else [puller_name]

    def check_processor_targets(self, processor_name: str, processor: ProcessorActor):
        """
        Check that targets of a processor exist in the dictionary of targets.
        If it is not the case, it raises a UnexistingActorException
        """
        for target_actor_name in self._get_processor_target_names(processor_name):
            if target_actor_name not in self.actors:
                raise UnexistingActorException(target_actor_name)

    def check_processors_targets_are_unique(self):
        """
        Check that processors targets are unique, i.e., the same target is not related to
        two different processors
        """
        used_targets = []
        for processor_name, _ in self.processors.items():
            for target_actor_name in self._get_processor_target_names(processor_name):
                if target_actor_name in used_targets:
                    raise TargetActorAlreadyUsed(target_actor_name)
                used_targets.append(target_actor_name)


class PreProcessorBindingManager(ProcessorBindingManager):
    """
    Class for management the binding between pullers and pre-processor actors
    """

    def __init__(self, config: dict | None = None, pullers: dict | None = None, processors: dict | None = None):
        """
        The PreProcessorBindingManager defines bindings between pullers and processors: puller->processor->dispatcher
        :param dict pullers: Dictionary of actors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        :param dict processors: Dictionary of processors with structure {<processor1_key>:processor1,
        <processor2_key>:processor2...}
        """
        super().__init__(actors=pullers, processors=processors, config=config)

    def process_bindings(self):
        """
        Define bindings between self.actors according to the pre-processors' targets.
        """
        self.check_processors_targets_are_unique()
        for processor_name, processor in self.processors.items():
            self.check_processor_targets(processor_name, processor)
            for target_actor_name in self._get_processor_target_names(processor_name):
                puller_actor = self.actors[target_actor_name]
                processor_proxy = processor.get_proxy()
                current_dispatchers = list(puller_actor.report_filter.dispatchers())
                for dispatcher in current_dispatchers:
                    processor.add_target_actor(dispatcher)
                    puller_actor.report_filter.replace(dispatcher, processor_proxy)

    def check_processor_targets(self, processor_name: str, processor: ProcessorActor):
        """
        Check that targets of a processor exist in the dictionary of targets.
        If it is not the case, it raises a UnexistingActorException
        It also checks that the actor is a PullerActor instance.
        If it is not the case, it raises UnsupportedActorTypeException
        """
        super().check_processor_targets(processor_name, processor)
        for target_actor_name in self._get_processor_target_names(processor_name):
            actor = self.actors[target_actor_name]
            if not isinstance(actor, PullerActor):
                raise UnsupportedActorTypeException(type(actor).__name__)
