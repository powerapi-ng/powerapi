# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
import sys

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
import tests

from powerapi.cli.parsing_manager import RootConfigParsingManager, \
    SubgroupConfigParsingManager
from powerapi.exception import AlreadyAddedArgumentException, BadTypeException, UnknownArgException, \
    MissingValueException, SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, \
    NoNameSpecifiedForSubgroupException, TooManyArgumentNamesException, AlreadyAddedSubparserException, \
    SameLengthArgumentNamesException, BadContextException
from powerapi.cli.config_parser import store_true, store_val
from tests.utils.cli.base_config_parser import load_configuration_from_json_file, \
    generate_cli_configuration_from_json_file


###############
# PARSER TEST #
###############
def test_add_argument_to_cli_parser_that_already_exist_raise_an_exception():
    """
    Tests if adding an argument that already exists to a parser raises an
    AlreadyAddedArgumentException
    """

    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a')

    with pytest.raises(AlreadyAddedArgumentException):
        parser_manager.add_argument_to_cli_parser('a')

    with pytest.raises(AlreadyAddedArgumentException):
        parser_manager.add_argument_to_cli_parser('help')

    assert len(parser_manager.cli_parser.arguments) == 3 # help argument + a argument


#####################
# MAIN PARSER TESTS #
#####################
def test_add_flag_arguments_with_short_name_to_cli_parser():
    """
    Test that adding flag arguments with a short name to cli parser modified short_arg string
    """
    parser_manager = RootConfigParsingManager()
    assert parser_manager.cli_parser.short_arg == 'h'
    parser_manager.add_argument_to_cli_parser('a', is_flag=True)
    parser_manager.add_argument_to_cli_parser('x', is_flag=True)
    assert parser_manager.cli_parser.short_arg == 'hax'


def test_add_flag_arguments_and_no_flag_arguments_with_short_name_to_cli_parser():
    """
    Test if adding arguments (flag and no flag) to the parser modified short_arg string.
    long_arg list is not changed
    """
    parser_manager = RootConfigParsingManager()
    assert parser_manager.cli_parser.short_arg == 'h'
    parser_manager.add_argument_to_cli_parser('a', is_flag=True)
    assert parser_manager.cli_parser.short_arg == 'ha'
    parser_manager.add_argument_to_cli_parser('b')
    assert parser_manager.cli_parser.short_arg == 'hab:'
    parser_manager.add_argument_to_cli_parser('c', is_flag=True)
    assert parser_manager.cli_parser.short_arg == 'hab:c'

    assert len(parser_manager.cli_parser.long_arg) == 1 # Only help is arg argument

    assert parser_manager.cli_parser.long_arg == ["help"]  # Only help is arg argument


def test_add_arguments_with_long_name_to_cli_parser():
    """
    Test if adding arguments with long name to cli parser modifies long_arg list.
    short_arg string is not changed
    """
    parser_manager = RootConfigParsingManager()
    assert parser_manager.cli_parser.long_arg == ['help']
    parser_manager.add_argument_to_cli_parser('aaa')
    assert parser_manager.cli_parser.long_arg == ['help', 'aaa=']
    parser_manager.add_argument_to_cli_parser('xx')
    assert parser_manager.cli_parser.long_arg == ['help', 'aaa=', 'xx=']

    assert parser_manager.cli_parser.short_arg == 'h'


def test_add_flag_arguments_with_long_name_to_cli_parser():
    """
    Test if adding a flag arguments with long to the parser modifies the long_arg list.
    short_arg string is not changed
    """
    parser_manager = RootConfigParsingManager()
    assert parser_manager.cli_parser.long_arg == ['help']
    parser_manager.add_argument_to_cli_parser('aaa', is_flag=True)
    assert parser_manager.cli_parser.long_arg == ['help', 'aaa']
    parser_manager.add_argument_to_cli_parser('tttt', is_flag=True)
    assert parser_manager.cli_parser.long_arg == ['help', 'aaa', 'tttt']

    assert parser_manager.cli_parser.short_arg == 'h'


# full parsing test #
def check_parse_cli_result(parser_manager: RootConfigParsingManager, input_str: str, outputs: dict):
    """
    Check that input_str is correctly parsed by parser
    """
    result = parser_manager._parse_cli(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_arguments_string_parsing_with_empty_parsing_manager():
    """
    Test to parse arguments provided as string with a parsing parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : UnknownArgException(a)
    - "-a --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    ConfigParsingManager description:

    - base parser arguments : None
    """
    parser_manager = RootConfigParsingManager()

    check_parse_cli_result(parser_manager, '', {})

    with pytest.raises(UnknownArgException):
        check_parse_cli_result(parser_manager, '-z', None)

    with pytest.raises(UnknownArgException):
        check_parse_cli_result(parser_manager, '-a', None)

    with pytest.raises(UnknownArgException):
        check_parse_cli_result(parser_manager, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parse_cli_result(parser_manager, '-b', None)


def test_arguments_dict_validation_with_empty_parsing_manager():
    """
    Test validation of arguments dictionary with a parsing manager and retrieve the following results:

    - "" : {}
    - "-z value" : UnknownArgException(z)
    - "-a 10 " : UnknownArgException(a)
    - "-a 10 --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    ConfigParsingManager description:

    - base parser arguments : None
    """
    parser_manager = RootConfigParsingManager()
    dic_z = {
        "z": "value"
    }

    dic_a = {
        "a": 10
    }

    dic_a_sub = {
        "a": 10,
        "sub" : {
            "type": "toto",
            "b": True
        }
    }

    dic_b = {
        "b": True
    }

    with pytest.raises(UnknownArgException):
        parser_manager.validate(dic_z)

    with pytest.raises(UnknownArgException):
        parser_manager.validate(dic_a)

    with pytest.raises(UnknownArgException):
        parser_manager.validate(dic_a_sub)

    with pytest.raises(UnknownArgException):
        parser_manager.validate(dic_b)


def test_arguments_dict_validation_with_parsing_manager(root_config_parsing_manager):
    """
    Test validation of arguments dictionary with a parsing manager and retrieve the following results:

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknownArgException(sub)
    - "-b" : UnknownArgException(b)

    ConfigParsingManager description:

    - base parser arguments : -a
    """

    dic_z = {
        "z": True
    }

    dic_a = {
        "a": True
    }

    dic_a_sub = {
        "a": True,
        "sub" : {
            "type": "toto",
            "b": True
        }
    }

    dic_b = {
        "b": True
    }

    with pytest.raises(UnknownArgException):
        root_config_parsing_manager.validate(dic_z)

    assert root_config_parsing_manager.validate(dic_a) == dic_a

    with pytest.raises(UnknownArgException):
        root_config_parsing_manager.validate(dic_a_sub)

    with pytest.raises(UnknownArgException):
        root_config_parsing_manager.validate(dic_b)


def test_arguments_string_parsing_with_subgroup_parser_in_parsing_manager(root_config_parsing_manager):
    """
    Test to parse arguments with a parsing manager containing a subgroup parser. It must retrieve the following
    results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForSubgroupException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    ConfigParsingManager description:

    - base parser arguments: -a
    - subgroup parser toto bound to the argument sub with sub arguments: -b and --name
    """

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('b', is_flag=True, action=store_true)
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    check_parse_cli_result(root_config_parsing_manager, "", {})

    with pytest.raises(UnknownArgException):
        check_parse_cli_result(root_config_parsing_manager, "-z", {})

    check_parse_cli_result(root_config_parsing_manager, '-a', {'a': True})

    with pytest.raises(NoNameSpecifiedForSubgroupException):
        check_parse_cli_result(root_config_parsing_manager, '-a --sub toto -b', {})

    check_parse_cli_result(root_config_parsing_manager, '-a --sub toto -b --name titi',
                           {'a': True, 'sub': {'titi': {'type': 'toto', 'b': True}}})

    with pytest.raises(BadContextException):
        check_parse_cli_result(root_config_parsing_manager, "-b", {})


def test_arguments_dict_validation_with_subgroup_parser_in_parsing_manager(root_config_parsing_manager):
    """
    Test to validate arguments with a parsing manager containing a subgroup parser. It must retrieve the following
    results:

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : UnknownArgException(b)

    ConfigParsingManager description:

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : -b and --name
    """
    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('b', is_flag=True, action=store_true)
    subparser.add_argument_to_cli_parser('type', is_flag=True, action=store_true)
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    dic_a = {'a': True}

    dic_z = {
        "z": True
    }

    dic_b = {
        'b': "type"
    }

    dic_a_sub = {
        'a': True,
        'sub': {
            'titi':
                {
                    'type': 'toto',
                    'b': "type"
                }
        }
    }

    with pytest.raises(UnknownArgException):
        root_config_parsing_manager.validate(dic_z)

    with pytest.raises(UnknownArgException):
        root_config_parsing_manager.validate(dic_b)

    assert root_config_parsing_manager.validate(dic_a) == dic_a

    assert root_config_parsing_manager.validate(dic_a_sub) == dic_a_sub

    assert root_config_parsing_manager.validate({}) == {}


def test_parsing_of_two_subgroups_of_the_same_type_with_parsing_manager(root_config_parsing_manager):
    """
    Test the parsing of two subgroups of the same type created with the following cli:
    --sub toto --name titi --sub toto -b --name tutu

    The result must be:
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """
    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('b', is_flag=True, action=store_true)
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    check_parse_cli_result(root_config_parsing_manager, '--sub toto --name titi --sub toto -b --name tutu',
                           {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}})


def test_validation_of_two_subgroups_of_the_same_type_in_parsing_manager(root_config_parsing_manager):
    """
    Test the validation of two subgroups of the same type created with the following cli:
    --sub toto --name titi --sub toto -b --name tutu

    The result must be:
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """
    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('type')
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    expected_dic = {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}}
    assert root_config_parsing_manager.validate(expected_dic) == expected_dic


def test_parsing_of_two_subgroups_of_different_type_in_parsing_manager(root_config_parsing_manager):
    """
    Test the validation of two subgroups of different type created with the following cli:
    Create two component with different type with the following cli :
    --sub toto --name titi --sub tutu --name tete

    The result must be:
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    """
    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParsingManager('tutu')
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    check_parse_cli_result(root_config_parsing_manager, '--sub toto --name titi --sub tutu --name tete',
                           {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}}})


def test_parsing_of_repeated_subgroups_in_parsing_manager_raise_an_exception(root_config_parsing_manager):
    """
    Test the parsing of two subgroups with same type and name created with the following cli:
    --sub toto --name titi --sub toto --name titi

    SubgroupAlreadyExistException must be raised
    """

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument_to_cli_parser('b', is_flag=True, action=store_true)
    subparser.add_argument_to_cli_parser('n', 'name')
    root_config_parsing_manager.add_subgroup_parser('sub', subparser)

    with pytest.raises(SubgroupAlreadyExistException):
        check_parse_cli_result(root_config_parsing_manager, '--sub toto --name titi --sub toto --name titi', None)


def test_arguments_string_parsing_with_and_without_val_in_parsing_manager(root_config_parsing_manager):
    """
    Test to parse arguments with and without value. The expected results are:

    - "-c" : MissingValue(c)
    - "-d" : MissingValue(d)
    - "-c 1" : {c : 1}
    - "-d 10" : {d : 10}

    ConfigParsingManager description:

    - base parser arguments: -a (flag), -c (no flag), -d (int)
    """

    root_config_parsing_manager.add_argument_to_cli_parser('c')

    root_config_parsing_manager.add_argument_to_cli_parser('d', argument_type=int)

    with pytest.raises(MissingValueException):
        check_parse_cli_result(root_config_parsing_manager, '-c', None)

    with pytest.raises(MissingValueException):
        check_parse_cli_result(root_config_parsing_manager, '-d', None)

    check_parse_cli_result(root_config_parsing_manager, '-c 1', {'c': '1'})

    check_parse_cli_result(root_config_parsing_manager, '-d 10', {'d': 10})


def test_validation_of_arguments_dict_parsing_with_val_in_parsing_manager(root_config_parsing_manager):
    """
    Test the validation of arguments with value. The expected results are:

    - "-c 1" : {c : 1}
    - "-d 89" : {d : 89}

    ConfigParsingManager description:

    - base parser arguments: -a (flag), -c (not flag), -d (int)
    """
    root_config_parsing_manager.add_argument_to_cli_parser('c')

    root_config_parsing_manager.add_argument_to_cli_parser('d', argument_type=int)

    dic_c = {'c': '1'}
    dic_d = {'d': 89}

    assert root_config_parsing_manager.validate(dic_c) == dic_c

    assert root_config_parsing_manager.validate(dic_d) == dic_d


def test_arguments_string_parsing_type_checking_in_parsing_manager(root_config_parsing_manager):
    """
    Test that the type of argument is correctly checked by the parsing manager when a string is used as input
    """
    root_config_parsing_manager.add_argument_to_cli_parser('c', argument_type=int)

    with pytest.raises(BadTypeException):
        check_parse_cli_result(root_config_parsing_manager, '-c string', {'c': 'string'})

    check_parse_cli_result(root_config_parsing_manager, '-c 1', {'c': 1})


def test_validation_of_arguments_dict_type_checking_in_parsing_manager(root_config_parsing_manager):
    """
        Test that the type of an argument is correctly validated by the parser when a dict is used as input
    """
    root_config_parsing_manager.add_argument_to_cli_parser('c', argument_type=int)

    str_dic = {'c': 'string'}
    int_dic = {'c': 42}

    with pytest.raises(BadTypeException):
        root_config_parsing_manager.validate(str_dic)

    assert root_config_parsing_manager.validate(int_dic) == int_dic


# multi name tests #
def test_arguments_string_parsing_with_long_and_short_names_in_parsing_manager(root_config_parsing_manager):
    """
    Test that arguments parsing only relates parsing result to long name in arguments with long and short names
    """
    root_config_parsing_manager.add_argument_to_cli_parser('c', 'coco')
    root_config_parsing_manager.add_argument_to_cli_parser('d', 'xx', argument_type=int)

    check_parse_cli_result(root_config_parsing_manager, '-c 1', {'coco': '1'})

    check_parse_cli_result(root_config_parsing_manager, '-d 555', {'xx': 555})


def test_add_arguments_with_two_short_names_raise_an_exception_in_parsing_manager(root_config_parsing_manager):
    """
    Test if adding arguments to a parser with two short names raise a SameLengthArgumentNamesException
    The arguments are not added
    """
    with pytest.raises(SameLengthArgumentNamesException):
        root_config_parsing_manager.add_argument_to_cli_parser('c', 'd')

    with pytest.raises(SameLengthArgumentNamesException):
        root_config_parsing_manager.add_argument_to_cli_parser('t', 's')

    assert len(root_config_parsing_manager.cli_parser.arguments) == 3 # --help and -h

    assert root_config_parsing_manager.cli_parser.long_arg == ['help']
    assert root_config_parsing_manager.cli_parser.short_arg == 'ha'

def test_add_arguments_with_two_long_names_raise_an_exception_in_parsing_manager(root_config_parsing_manager):
    """
    Test if adding arguments to a parser with long names raise a SameLengthArgumentNamesException.
    The arguments are not added
    """
    with pytest.raises(SameLengthArgumentNamesException):
        root_config_parsing_manager.add_argument_to_cli_parser('coco', 'dodo')

    with pytest.raises(SameLengthArgumentNamesException):
        root_config_parsing_manager.add_argument_to_cli_parser('ddddd', 'plplp')

    assert len(root_config_parsing_manager.cli_parser.arguments) == 3 # -a, --help and -h

    assert root_config_parsing_manager.cli_parser.long_arg == ['help']
    assert root_config_parsing_manager.cli_parser.short_arg == 'ha'


# Type tests #
def test_add_argument_with_default_type_in_parsing_manager():
    """
    Test if adding arguments without type has string (default type) as type
    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a')
    parser_manager.add_argument_to_cli_parser('b')
    result_a = parser_manager.parse('python -a 1'.split())
    result_b = parser_manager.parse('python3 -b string'.split())
    assert len(result_a) == 1
    assert 'a' in result_a
    assert isinstance(result_a['a'], str)

    assert len(result_b) == 1
    assert 'b' in result_b
    assert isinstance(result_b['b'], str)


def test_add_argument_with_type_in_parsing_manager():
    """
    Test if adding arguments with a type have currently this type

    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a', argument_type=int)
    parser_manager.add_argument_to_cli_parser('b', argument_type=bool)

    result = parser_manager.parse('python -a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)

    result = parser_manager.parse('python3 -b false'.split())
    assert len(result) == 1
    assert 'b' in result
    assert isinstance(result['b'], bool)


def test_parsing_of_arguments_string_with_wrong_type_raise_an_exception_in_parsing_manager():
    """
    Test that parsing arguments with a wront value type raises a BadTypeException
    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a', argument_type=int)

    with pytest.raises(BadTypeException):
        parser_manager._parse_cli('-a a'.split())



# parse with Subparser tests #
def test_add_subgroup_parser_that_already_exists_raises_an_exception_in_parsing_manager():
    """
    Test that adding a subgroup parser that already exists raises an
    AlreadyAddedSubparserException
    """
    parser_manager = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')
    subparser.add_argument_to_cli_parser('n', 'name')
    parser_manager.add_subgroup_parser('toto', subparser)

    repeated_subparser = SubgroupConfigParsingManager('titi')
    repeated_subparser.add_argument_to_cli_parser('n', 'name')

    with pytest.raises(AlreadyAddedSubparserException):
        parser_manager.add_subgroup_parser('toto', repeated_subparser)


def test_parsing_of_arguments_string_with_subgroup_parser_with_long_and_short_arguments_names_in_parsing_manager():
    """
    Tests that parsing arguments of a subgroup parser with long and short names arguments
    only binds parser results to the long name
    """
    parser_manager = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')
    subparser.add_argument_to_cli_parser('a', 'aaa', is_flag=True, action=store_true, default_value=False)
    subparser.add_argument_to_cli_parser('c', 'ttt', is_flag=False, action=store_val, argument_type=int)
    subparser.add_argument_to_cli_parser('n', 'name')
    parser_manager.add_subgroup_parser('sub', subparser)
    check_parse_cli_result(parser_manager, '--sub titi -a --name tutu -c 15', {'sub': {'tutu':
                                                                                      {'aaa': True,
                                                                                       'type': 'titi',
                                                                                       'ttt': 15}}})


def test_add_subgroup_parser_without_name_argument_raise_an_exception_in_parsing_manager():
    """
    Test that adding a subgroup parser with no argument 'name' raises a
    SubgroupParserWithoutNameArgumentException
    """
    parser = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')

    with pytest.raises(SubgroupParserWithoutNameArgumentException):
        parser.add_subgroup_parser('toto', subparser)


def test_parsing_empty_string_return_default_values_of_arguments_in_parsing_manager():
    """
    Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('a', default_value=1)
    parser_manager.add_argument_to_cli_parser('xxx', default_value='val')
    result = parser_manager._parse_cli(''.split())
    assert len(result) == 2
    assert 'a' in result
    assert 'xxx' in result
    assert result['a'] == 1
    assert result['xxx'] == 'val'


def test_validate_empty_dict_return_default_values_of_arguments_in_parsing_manager():
    """
    Test that the result of parsing an empty dict is a dict of arguments with their default value
    """
    parser_manager = RootConfigParsingManager()
    parser_manager.add_argument_to_cli_parser('c', argument_type=int, default_value=1)
    parser_manager.add_argument_to_cli_parser('hello', argument_type=str, default_value="world")

    default_dic = {}
    expected_dic = {'c': 1, 'hello': 'world'}

    assert parser_manager.validate(default_dic) == expected_dic


def test_parsing_configuration_file_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a json file containing a configuration is correctly parsed
    """
    config_file = 'root_manager_basic_configuration.json'
    expected_dict = load_configuration_from_json_file(config_file)

    result = root_config_parsing_manager_with_mandatory_arguments.parse(args=('--config-file ' + test_files_path +
                                                                    '/' + config_file).split())
    assert  result == expected_dict


def test_parsing_configuration_file_with_long_and_short_names_for_arguments_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a json file containing a configuration with long and short names for arguments is correctly parsed
    """
    config_file = 'root_manager_basic_configuration_with_long_and_short_names.json'
    expected_dict = load_configuration_from_json_file(config_file)
    expected_dict['argumento2'] = expected_dict.pop('2')
    expected_dict['arg5'] = expected_dict.pop('5')

    result = root_config_parsing_manager_with_mandatory_arguments.parse(args=('--config-file ' + test_files_path +
                                                                    '/' + config_file).split())
    assert  result == expected_dict


def test_parsing_configuration_file_with_no_argument_with_default_value_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a json file containing a configuration with no values for arguments with default values
    is correctly parsed
    """
    config_file = 'root_manager_basic_configuration_with_no_argument_with_default_value.json'
    expected_dict = load_configuration_from_json_file(config_file)
    expected_dict['arg5'] = 'default value'
    result = root_config_parsing_manager_with_mandatory_arguments.parse(args=('--config-file ' + test_files_path +
                                                                    '/' + config_file).split())

    assert  result == expected_dict

def test_parsing_configuration_file_with_unknown_argument_terminate_execution_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a json file containing a configuration with unknown arguments stops execution of the application
    """
    config_file = 'root_manager_basic_configuration_with_unknown_argument.json'

    result = None
    with pytest.raises(SystemExit) as result:
        _ = root_config_parsing_manager_with_mandatory_arguments.parse(args=('--config-file ' + test_files_path +
                                                                    '/' + config_file).split())

    assert result.type == SystemExit
    assert result.value.code == -1


def test_parsing_configuration_file_with_wrong_argument_terminate_execution_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a json file containing a configuration with unknown arguments stops execution of the application
    """
    config_file = 'root_manager_basic_configuration_with_argument_type_value.json'

    result = None
    with pytest.raises(SystemExit) as result:
        _ = root_config_parsing_manager_with_mandatory_arguments.parse(args=('--config-file ' + test_files_path +
                                                                    '/' + config_file).split())

    assert result.type == SystemExit
    assert result.value.code == -1

def test_parsing_cli_configuration_in_parsing_manager(root_config_parsing_manager_with_mandatory_arguments):
    """
    Test that a list of strings containing a configuration is correctly parsed
    """
    config_file = 'root_manager_basic_configuration.json'
    sys.argv = generate_cli_configuration_from_json_file(file_name=config_file)
    expected_dict = load_configuration_from_json_file(config_file)

    result = root_config_parsing_manager_with_mandatory_arguments.parse()
    assert  result == expected_dict


def test_parsing_cli_configuration_with_long_and_short_names_for_arguments_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments):
    """
    Test that a list of strings containing a configuration with long and short names for arguments is correctly parsed
    """
    config_file = 'root_manager_basic_configuration_with_long_and_short_names.json'
    sys.argv = generate_cli_configuration_from_json_file(file_name=config_file)
    expected_dict = load_configuration_from_json_file(config_file)
    expected_dict['argumento2'] = expected_dict.pop('2')
    expected_dict['arg5'] = expected_dict.pop('5')

    result = root_config_parsing_manager_with_mandatory_arguments.parse()
    assert  result == expected_dict

def test_parsing_cli_configuration_with_no_argument_with_default_value_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments):
    """
    Test that a list of strings containing a configuration with no values for arguments with default values
    is correctly parsed
    """
    config_file = 'root_manager_basic_configuration_with_no_argument_with_default_value.json'
    sys.argv = generate_cli_configuration_from_json_file(file_name=config_file) #['test', '--argument1', '5', '-2', 'this is a mandatory argument', '--argument3', 'false', '--arg4', '10.5']

    expected_dict = load_configuration_from_json_file(config_file)

    expected_dict['arg5'] = 'default value'
    result = root_config_parsing_manager_with_mandatory_arguments.parse()

    assert  result == expected_dict

def test_parsing_cli_configuration_with_unknown_argument_terminate_execution_in_parsing_manager(
        root_config_parsing_manager_with_mandatory_arguments, test_files_path):
    """
    Test that a list of strings containing a configuration with unknown arguments stops execution of the application
    """
    config_file = 'root_manager_basic_configuration_with_unknown_argument.json'
    sys.argv = generate_cli_configuration_from_json_file(file_name=config_file)

    result = None
    with pytest.raises(SystemExit) as result:
        _ = root_config_parsing_manager_with_mandatory_arguments.parse()

    assert result.type == SystemExit
    assert result.value.code == -1
