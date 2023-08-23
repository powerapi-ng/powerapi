# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
# All rights reserved.

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
import pytest

from powerapi.cli import ConfigValidator
from powerapi.exception import NotAllowedArgumentValueException, MissingArgumentException, FileDoesNotExistException, \
    UnexistingActorException
from tests.utils.cli.base_config_parser import load_configuration_from_json_file


def test_config_in_stream_mode_with_csv_input_raise_an_exception(invalid_csv_io_stream_config):
    """
    Test that an invalid configuration with stream mode enabled and csv as input is detected by the ConfigValidator
    """
    with pytest.raises(NotAllowedArgumentValueException):
        ConfigValidator.validate(invalid_csv_io_stream_config)


def test_config_in_postmortem_mode_with_csv_input_is_validated(create_empty_files_from_config,
                                                               csv_io_postmortem_config):
    """
    Test that a valid configuration is detected by the ConfigValidator when stream mode is disabled.
    The files list for the input has to be transformed into a list
    """
    try:
        expected_result = load_configuration_from_json_file(
            file_name='csv_input_output_stream_mode_enabled_configuration.json')
        for current_input in expected_result['input']:
            if expected_result['input'][current_input]['type'] == 'csv':
                expected_result['input'][current_input]['files'] = (
                    expected_result['input'][current_input]['files']).split(',')

        expected_result['stream'] = False

        ConfigValidator.validate(csv_io_postmortem_config)

        assert csv_io_postmortem_config == expected_result

    except NotAllowedArgumentValueException:
        assert False


def test_valid_config_postmortem_csv_input_without_optional_arguments_is_validated(create_empty_files_from_config,
                                                                                   csv_io_postmortem_config_without_optional_arguments):
    """
    Test that a valid configuration is detected by the ConfigValidator when stream mode is disabled.
    Default values has to be defined and the files list for the input has to be transformed into a list
    """
    expected_result = csv_io_postmortem_config_without_optional_arguments.copy()
    for current_input in expected_result['input']:
        if expected_result['input'][current_input]['type'] == 'csv':
            expected_result['input'][current_input]['files'] = (expected_result['input'][current_input]['files']).split(
                ',')
        expected_result['input'][current_input]['name'] = 'default_puller'
        expected_result['input'][current_input]['model'] = 'HWPCReport'
    expected_result['stream'] = False
    expected_result['verbose'] = False

    ConfigValidator.validate(csv_io_postmortem_config_without_optional_arguments)

    assert csv_io_postmortem_config_without_optional_arguments == expected_result


def test_config_with_csv_input_with_files_that_do_not_exist_raise_an_exception(csv_io_postmortem_config):
    """
    Test that validation of a configuration indicating files that do not exist in csv as input raises a
    FileDoesNotExistException
    """
    with pytest.raises(FileDoesNotExistException) as raised_exception:
        ConfigValidator.validate(csv_io_postmortem_config)

    assert raised_exception.value.file_name == '/tmp/rapl.csv'


def test_config_without_inputs_raise_an_exception(config_without_input):
    """
    Test that validation of an invalid configuration without inputs raises a MissingArgumentException
    """
    with pytest.raises(MissingArgumentException) as raised_exception:
        ConfigValidator.validate(config_without_input)

    assert raised_exception.value.argument_name == 'input'


def test_config_without_outputs_raise_an_exception(config_without_output):
    """
    Test that validation of an invalid configuration without outputs raises a MissingArgumentException
    """
    with pytest.raises(MissingArgumentException) as raised_exception:
        ConfigValidator.validate(config_without_output)

    assert raised_exception.value.argument_name == 'output'


def test_config_with_processor_but_without_binding_raise_an_exception(puller_to_processor_config_without_bindings):
    """
    Test that validation of a configuration with processors but without binding raises a
    """
    with pytest.raises(MissingArgumentException) as raised_exception:
        ConfigValidator.validate(puller_to_processor_config_without_bindings)

    assert raised_exception.value.argument_name == 'binding'


def test_config_without_processor_but_with_binding_raise_an_exception(puller_to_processor_config_without_processors):
    """
    Test that validation of a configuration without processors but with binding raises a
    """
    with pytest.raises(MissingArgumentException) as raised_exception:
        ConfigValidator.validate(puller_to_processor_config_without_processors)

    assert raised_exception.value.argument_name == 'processor'


def test_config_with_processor_and_binding_with_unexisting_from_actor_raise_an_exception(
        not_existent_puller_to_processor_configuration):
    """
    Test that validation of a configuration with unexisting actors raise an exception
    """
    with pytest.raises(UnexistingActorException) as raised_exception:
        ConfigValidator.validate(not_existent_puller_to_processor_configuration)

    assert raised_exception.value.actor_path == not_existent_puller_to_processor_configuration['binding']['b1']['from']


def test_validation_of_correct_configuration_with_processors_and_bindings(output_input_configuration):
    """
    Test that a correct configuration with processors and bindings passes the validation
    """
    try:
        ConfigValidator.validate(output_input_configuration)
    except Exception:
        assert False

    assert True


def test_validation_of_correct_configuration_without_processors_and_bindings(output_input_configuration):
    """
    Test that a correct configuration without processors and bindings passes the validation
    """
    try:
        ConfigValidator.validate(output_input_configuration)
    except Exception:
        assert False

    assert True
