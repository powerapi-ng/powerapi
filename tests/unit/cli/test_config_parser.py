# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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

from powerapi.cli.config_parser import ConfigurationArgument, BaseConfigParser, RootConfigParser, SubgroupConfigParser
from powerapi.cli.config_parser import store_true, store_val
from powerapi.exception import AlreadyAddedArgumentException, BadTypeException, UnknownArgException, \
    BadContextException, MissingValueException, SubgroupAlreadyExistException, \
    SubgroupParserWithoutNameArgumentException, \
    NoNameSpecifiedForSubgroupException, TooManyArgumentNamesException, MissingArgumentException, \
    SameLengthArgumentNamesException, AlreadyAddedSubgroupException

from tests.utils.cli.base_config_parser import load_configuration_from_json_file, \
    generate_configuration_tuples_from_json_file, define_environment_variables_configuration_from_json_file, \
    remove_environment_variables_configuration


###############
# PARSER TEST #
###############
def test_add_argument_that_already_exists():
    """
    Test if an AlreadyAddedArgumentException is raised when an argument that already exists is added to a
    BaseConfigParser
    """

    parser = BaseConfigParser()
    parser.add_argument('a')
    parser.add_argument('bb', 'bbb', 'b', 'bbbbbb')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('a')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('bbb')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('bbbbbb')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('ccc', 'a')

    assert len(parser.arguments) == 5


def test_get_arguments_returns_all_stored_arguments():
    """
    Test if all the arguments are correctly stored by BasePaserConfig
    """
    longest_name_arg_a = 'aaa'
    name_arg_a_1 = 'a'
    name_arg_a_2 = 'ab'
    expected_argument_a = ConfigurationArgument(names=[name_arg_a_1, longest_name_arg_a, name_arg_a_2],
                                                argument_type=bool, default_value=False,
                                                help_text='This a parameter', is_mandatory=False, is_flag=True)

    longest_name_arg_xx = 'XXXX'
    name_arg_xx_1 = 'xx'
    name_arg_xx_2 = 'xax'
    expected_argument_xx = ConfigurationArgument(names=[name_arg_xx_1, longest_name_arg_xx, name_arg_xx_2],
                                                 argument_type=str, default_value='Hi',
                                                 help_text='This is another parameter', is_mandatory=True,
                                                 is_flag=False, action=store_val)

    parser = BaseConfigParser()
    parser.add_argument(name_arg_a_1, longest_name_arg_a, name_arg_a_2, is_mandatory=expected_argument_a.is_mandatory,
                        is_flag=expected_argument_a.is_flag,
                        argument_type=expected_argument_a.type, help_text=expected_argument_a.help_text,
                        default_value=expected_argument_a.default_value)

    parser.add_argument(name_arg_xx_1, longest_name_arg_xx, name_arg_xx_2,
                        is_mandatory=expected_argument_xx.is_mandatory, is_flag=expected_argument_xx.is_flag,
                        argument_type=expected_argument_xx.type, help_text=expected_argument_xx.help_text,
                        default_value=expected_argument_xx.default_value)

    arguments = parser.get_arguments()

    assert len(arguments) == 6

    assert longest_name_arg_a in arguments

    assert longest_name_arg_xx in arguments

    assert expected_argument_a == arguments.get(longest_name_arg_a)

    assert expected_argument_xx == arguments.get(longest_name_arg_xx)


def test_get_mandatory_arguments_return_all_mandatory_argument(base_config_parser):
    """
    Test that all the mandatory arguments are identified by the paser
    """
    expected_mandatory_args_names = ['arg2', 'arg4']

    mandatory_args = base_config_parser._get_mandatory_arguments()

    assert len(mandatory_args) == len(expected_mandatory_args_names)

    for expected_mandatory_args_name in expected_mandatory_args_names:
        is_present = False
        for mandatory_arg in mandatory_args:
            if expected_mandatory_args_name in mandatory_arg.names:
                is_present = True
                break
        assert is_present


def test_get_mandatory_arguments_return_empty_list_with_no_mandatory_args(base_config_parser_no_mandatory_arguments):
    """
    Test that mandatory arguments list is empty if parser does not have mandatory arguments
    """
    mandatory_args = base_config_parser_no_mandatory_arguments._get_mandatory_arguments()

    assert not mandatory_args


def test_validate_check_mandatory_arguments_on_configuration(base_config_parser):
    """
    Test if mandatory arguments are verified by the parser
    """
    conf = load_configuration_from_json_file('basic_configuration.json')
    conf_without_mandatory_arguments = \
        load_configuration_from_json_file('basic_configuration_without_mandatory_arguments.json')

    try:
        validated_config = base_config_parser.validate(conf)
        assert validated_config == conf

    except MissingArgumentException:
        assert False

    with pytest.raises(MissingArgumentException):
        _ = base_config_parser.validate(conf_without_mandatory_arguments)


def test_validate_accept_configuration_when_no_mandatory_arguments_exist(base_config_parser_no_mandatory_arguments):
    """
    Test if a configuration passes the validation if there is no mandatory argument
    """
    conf = load_configuration_from_json_file('basic_configuration_without_mandatory_arguments.json')

    try:
        validated_config = base_config_parser_no_mandatory_arguments.validate(conf)
        assert validated_config == conf

    except MissingArgumentException:
        assert False


def test_validate_adds_default_values_for_no_arguments_defined_in_configuration_that_have_one(base_config_parser):
    """
    Test if parser add default values for arguments that are not in configuration and that have one
    """
    conf = load_configuration_from_json_file('basic_configuration_without_arguments_with_default_values.json')

    expected_conf = conf.copy()
    expected_conf['arg1'] = 3
    expected_conf['arg5'] = 'default value'

    validated_config = base_config_parser.validate(conf)
    assert validated_config == expected_conf


def test_get_arguments_str_return_str_with_all_information(base_config_parser, base_config_parser_str_representation):
    """
    Test that the parser is able to return a string with all the information related to it in a correct format
    """

    arguments_str = base_config_parser._get_arguments_str(' ')

    assert arguments_str == base_config_parser_str_representation


def test_parser_return_correct_values_for_each_argument(base_config_parser):
    """
    Test that the _parser method return correct values for different arguments in configuration
    """

    args = generate_configuration_tuples_from_json_file('basic_configuration.json')
    acc = {}

    expected_acc = {'argumento1': 5,
                    "argumento2": "this a mandatory argument",
                    "argument3": False,
                    "dded": 10.5}

    args, acc = base_config_parser._parse(args, acc)

    assert not args
    assert acc == expected_acc


def test_parser_raise_an_exception_with_an_unknown_argument(base_config_parser):
    """
    Test that the _parser method return correct values for different arguments in configuration
    """

    args = generate_configuration_tuples_from_json_file('basic_configuration.json')
    args.append(('unknown_arg', 'This is a new argument'))
    acc = {}

    with pytest.raises(NotImplementedError):
        _, _ = base_config_parser._parse(args, acc)


#####################
# ROOT PARSER TESTS #
#####################
# Test add_argument optargs #


def test_add_short_argument():
    """
    Test if an argument when a short name is added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a')
    assert parser.short_arg == 'a:'

    assert len(parser.arguments) == 1


def test_add_flag_argument_with_short_name():
    """
    Test if a flag argument with a short name was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'

    assert len(parser.arguments) == 1


def test_add_several_arguments_with_short_names():
    """
    Test if the arguments were added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'
    parser.add_argument('b', is_flag=True)
    assert parser.short_arg == 'ab'
    parser.add_argument('c')
    assert parser.short_arg == 'abc:'
    parser.add_argument('d')
    assert parser.short_arg == 'abc:d:'
    parser.add_argument('e')
    parser.add_argument('f')
    parser.add_argument('g')
    assert parser.short_arg == 'abc:d:e:f:g:'

    assert len(parser.arguments) == 7


def test_add_argument_with_two_short_names_raise_an_exception():
    """
    Test if adding an argument with two short names raises a SameLengthArgumentNamesException
    """
    parser = RootConfigParser(help_arg=False)

    with pytest.raises(SameLengthArgumentNamesException):
        parser.add_argument('a', 'b')

    assert parser.short_arg == ''
    assert not parser.arguments


def test_add_argument_with_long_name():
    """
    Test if an argument with a long name is added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa')
    assert parser.long_arg == ['aaa=']

    assert len(parser.arguments) == 1


def test_add_flag_argument_with_long():
    """
    Test if a flag argument with a long name is added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa', is_flag=True)
    assert parser.long_arg == ['aaa']

    assert len(parser.arguments) == 1


def test_add_argument_with_more_than_two_names_raise_an_exception():
    """
    Test if adding an argument with more than two names raises a TooManyArgumentNamesException
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('aaa', 'bbb', 'ccc', is_flag=True)

    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('aaa', 'b', 'c')

    assert not parser.long_arg
    assert not parser.arguments


# full parsing test #

def check_parsing_result(parser, input_str, outputs):
    """
    Check that input_str is correctly parsed by parser
    """
    result = parser.parse(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_parsing_of_config_of_empty_parser():
    """
    Test the parsing of strings with an empty base parser and retrieve the following results:

    - "": {}
    - "-z": UnknownArgException(z)
    - "-a": UnknownArgException(a)
    - "-a --sub toto -b": UnknownArgException(a)
    - "-b": UnknownArgException(b)

    Parser description:

    - root parser arguments: None
    """
    parser = RootConfigParser(help_arg=False)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-b', None)


def test_parsing_of_config_of_a_parser():
    """
    Test the parsing of strings with a not empty root parser and retrieve the following results:

    - "": {}
    - "-z": UnknownArgException(z)
    - "-a": {a: True}
    - "-a --sub toto -b": UnknownArgException(sub)
    - "-b": UnknownArgException(b)

    Parser description:

    - root parser arguments: -a
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', is_flag=True, action=store_true)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    check_parsing_result(parser, '-a', {'a': True})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-b', None)


def test_parsing_of_config_of_a_parser_with_a_subgroup_parser():
    """
    Test the parsing of strings with a not empty rooy parser and retrieve the following results:

    - "" : {}
    - "-z": UnknownArgException(z)
    - "-a": {a: True}
    - "-a --sub toto -b": NoNameSpecifiedForSubgroupException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b": BadContextException(b, [toto])

    Parser description:

    - root parser arguments: -a
    - subparser toto bound to the argument sub with sub arguments: -b and --name
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', is_flag=True, action=store_true)
    parser.add_subgroup(subgroup_type='sub')

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser(subgroup_type='sub', subgroup_parser=subparser)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    check_parsing_result(parser, '-a', {'a': True})

    with pytest.raises(NoNameSpecifiedForSubgroupException):
        check_parsing_result(parser, '-a --sub toto -b', {})

    check_parsing_result(parser, '-a --sub toto -b --name titi',
                         {'a': True, 'sub': {'titi': {'type': 'toto', 'b': True}}})

    with pytest.raises(BadContextException):
        check_parsing_result(parser, '-b', None)


def test_parsing_of_config_with_several_subgroups_with_the_same_name_in_a_parser_with_a_subgroup_parser():
    """
    Test the parsing of several subgroups with the same name. The result is:
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}, 'tata': {'type': 'toto'}}}

    The subgroups are created with the following cli:
    --sub toto --name titi --sub toto -b --name tutu --sub toto --name tata

    Parser description:

    - root parser arguments: None
    - subparser toto bound to the argument sub with sub arguments: -b and -n --name

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_subgroup(subgroup_type='sub')

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser(subgroup_type='sub', subgroup_parser=subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub toto -b --name tutu --sub toto --name tata',
                         {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True},
                                  'tata': {'type': 'toto'}}})


def test_parsing_of_several_subgroups_with_different_name_in_a_parser_with_several_subgroup_parsers():
    """
    Test the parsing of several subgroups with different name. The result is:
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    The subgroups are created with the following cli:
    --sub toto --name titi --sub tutu --name tete --sub tata --name tate

    Parser description:

    - root parser arguments: None
    - subparser toto bound to the argument sub with sub argument: -n --name
    - subparser tutu bound to the argument sub with sub argument: -n --name
    - subparser tata bound to the argument sub with sub argument: -n --name
    """
    parser = RootConfigParser(help_arg=False)

    parser.add_subgroup(subgroup_type='sub')

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParser('tutu')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParser('tata')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub tutu --name tete --sub tata --name tate',
                         {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}, 'tate': {'type': 'tata'}}})


def test_parsing_of_config_with_repeated_subgroups_names_raise_an_exception():
    """
    Test if an SubgroupAlreadyExistException is raised with two subgroups of the same name.
    The subgroups are created with the following cli:
    --sub toto --name titi --sub toto --name titi

    Parser description:

    - root parser arguments: None
    - subparser toto bound to the argument sub with sub arguments: -b (flag) and -n --name
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_subgroup(subgroup_type='sub')

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    with pytest.raises(SubgroupAlreadyExistException):
        check_parsing_result(parser, '--sub toto --name titi --sub toto --name titi', None)


def test_parsing_of_argument_with_val():
    """
    Test the parsing of strings with a root parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    Parser description :

    - root parser arguments : -c (not flag)
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c')

    with pytest.raises(MissingValueException):
        check_parsing_result(parser, '-c', None)

    check_parsing_result(parser, '-c 1', {'c': '1'})


# multi name tests #
def test_parsing_of_argument_with_long_short_names_and_val():
    """
    Test if the parsing of an argument with long and short names and a value works correctly.
    The value is only bound to the long name in the parsing result.

    Parser description:

    - root parser arguments: -c --coco

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c', 'coco')

    check_parsing_result(parser, '-c 1', {'coco': '1'})


def test_add_argument_with_two_long_names_with_same_length_raise_an_exception():
    """
    Test if the parser raise an exception SameLengthArgumentNamesException when a
    long argument with the same length is added. No subgroup parse must be added

    Parser description:

    - root parser arguments: None

    """
    parser = RootConfigParser(help_arg=False)
    with pytest.raises(SameLengthArgumentNamesException):
        parser.add_argument('coco', 'dodo')

    assert len(parser.arguments) == 0


# Type tests #
def test_parsing_arguments_with_val_has_correct_default_type():
    """
    Test if parsing arguments created with default type have default type in the parsing result.

    Parser description:

    - root parser arguments: -a, -b --bb, -c --cc
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a')
    parser.add_argument('b', 'bb')
    parser.add_argument('c', 'cc')
    result = parser.parse('-a 1 --bb string -c string_again'.split())
    assert len(result) == 3
    assert 'a' in result
    assert isinstance(result['a'], str)
    assert result['a'] == '1'

    assert 'bb' in result
    assert isinstance(result['bb'], str)
    assert result['bb'] == 'string'

    assert 'cc' in result
    assert isinstance(result['cc'], str)
    assert result['cc'] == 'string_again'


def test_parsing_arguments_with_val_has_correct_type():
    """
    Test if parsing arguments created with no default type have correct type in the parsing result.

    Parser description:

    - root parser arguments: -a, -b --bb, -c --cc

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', argument_type=int)
    result = parser.parse('-a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)


def test_parsing_argument_with_wrong_type_raise_an_exception():
    """
    Test if parsing arguments with a given value that can be parsed to the defined type raises an exception

    Parser description:

    - root parser arguments: -a --xx
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', 'xx', argument_type=int)

    with pytest.raises(BadTypeException):
        parser.parse('-a a'.split())

    with pytest.raises(BadTypeException):
        parser.parse('--xx toto'.split())


# parse with ComponentSubparser tests #
def test_add_subgroup_parser_that_already_exist_raise_an_exception():
    """
    Test if adding a subgroup parser that already exists raises an AlreadyAddedArgumentException.
    The subgroup parsers of root parser must not be affected

    Parser description:

    - root parser arguments: None
    - subparser titi bound to the argument toto with sub arguments: -n
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_subgroup(subgroup_type='toto')
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('n', 'name')

    repeated_subparser = SubgroupConfigParser('titi')
    repeated_subparser.add_argument('n', 'name')
    repeated_subparser.add_argument('arg2', 'a')

    parser.add_subgroup_parser('toto', subparser)

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_subgroup_parser('toto', repeated_subparser)

    assert len(parser.subgroup_parsers) == 1
    assert len(parser.subgroup_parsers['toto'].subparsers['titi'].arguments) == 2


def test_add_subgroup_parser_with_argument_name_work():
    """
    Test if adding a subgroup parser with a name argument works
    Parser description:

    - root parser arguments: None
    - subparser titi bound to the argument sub with sub arguments: -a --aaa, -n --name
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_subgroup(subgroup_type='sub')
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('a', 'aaa', is_flag=True, action=store_true, default_value=False)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    assert len(parser.subgroup_parsers) == 1
    assert len(parser.subgroup_parsers['sub'].subparsers['titi'].arguments) == 4
    assert 'a' in parser.subgroup_parsers['sub'].subparsers['titi'].arguments
    assert 'aaa' in parser.subgroup_parsers['sub'].subparsers['titi'].arguments
    assert 'n' in parser.subgroup_parsers['sub'].subparsers['titi'].arguments
    assert 'name' in parser.subgroup_parsers['sub'].subparsers['titi'].arguments


def test_add_subgroup_parser_without_argument_name_raise_an_exception():
    """
    Test if adding a subgroup parser with no argument 'name' raises a
    SubgroupParserWithoutNameArgumentException
    Parser description:

    - root parser arguments: None
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')

    with pytest.raises(SubgroupParserWithoutNameArgumentException):
        parser.add_subgroup_parser('toto', subparser)

    assert len(parser.subgroup_parsers) == 0


def test_parsing_empty_string_return_an_empty_dict():
    """
    Test that the result of parsing an empty string is an empty dict

    Parser description:

    - root parser arguments: -a, -b

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', default_value=1)
    parser.add_argument('b', default_value=False, argument_type=bool)
    result = parser.parse(''.split())
    assert len(result) == 0


def test_parsing_dict_return_configuration_with_arguments_long_name(
        root_config_parser_with_mandatory_and_optional_arguments,
        test_files_path):
    """
    Test that the result of parsing a dictionary configuration with long and short names for arguments
    returns a dictionary configuration only with long names for arguments

    Parser description:

    - root parser arguments: -a, -1 --argument1, -2 --argumento2, --arg3 --argument3, -d --arg4, --arg5 -5

    """
    config_file = 'root_manager_basic_configuration_with_long_and_short_names.json'
    expected_result = load_configuration_from_json_file(config_file)
    expected_result['argumento2'] = expected_result.pop('2')
    expected_result['arg5'] = expected_result.pop('5')

    result = root_config_parser_with_mandatory_and_optional_arguments.parse_config_dict(
        file_name=test_files_path + '/' + config_file)
    assert result == expected_result


############################
# SUBGROUP_PARSER TEST     #
############################
def test_subgroup_parser_empty(subgroup_parser):
    """
    Test subgroup parser on an empty token list.
    Must return an empty dictionary as parse result and an empty token
    list
    """
    assert subgroup_parser.parse([]) == ([], {})


def test_subgroup_parser_parsing_an_argument(subgroup_parser):
    """
    Test component_subparser, parse a token list which contain only subparser
    argument [('a', '')].

    must return return a  dictionary {'a':''} as parse result
    and an empty token list

    """
    assert subgroup_parser.parse([('a', '')]) == ([], {'a': None})


def test_subgroup_parsing_parser_several_arguments(subgroup_parser):
    """
    Test subgroup parser parses a token list which contains subparser
    argument and arguments from other parser[('a', ''), ('b', '')].

    must return a dictionary {'a':''} as parse result
    and a token list that contains the unparsed arguments : [('b', '')].

    """
    assert subgroup_parser.parse([('a', ''), ('b', '')]) == ([('b', '')],
                                                             {'a': None})


def test_subgroup_parser_parsing_empty_argument_list_return_an_empty_dict():
    """
    Test that the result of parsing an empty string is an empty dict
    """
    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('a', default_value=1)
    subparser.add_argument('x', default_value=False)
    acc, result = subparser.parse([])
    assert len(result) == 0


def test_normalize_configuration_dict_select_long_names_for_every_argument_in_config(base_config_parser):
    """
    Test that every argument in a configuration has at the end its long name after the normalization
    """
    conf = load_configuration_from_json_file(file_name='basic_configuration_with_long_and_short_names.json')
    expected_conf = load_configuration_from_json_file(file_name='basic_configuration.json')
    expected_conf['argumento1'] = expected_conf.pop('arg1')
    expected_conf['arg5'] = conf['5']
    expected_conf['dded'] = expected_conf.pop('arg4')

    result = base_config_parser.normalize_configuration(conf=conf)

    assert result == expected_conf


def test_normalize_configuration_dict_select_long_names_for_every_argument_in_config_for_root_config_parser(
        root_config_parser_with_mandatory_and_optional_arguments):
    """
    Test that every argument in a configuration has at the end its long name after the normalization
    """
    conf = load_configuration_from_json_file(file_name='basic_configuration_with_long_and_short_names.json')
    expected_conf = load_configuration_from_json_file(file_name='basic_configuration.json')
    expected_conf['argument1'] = expected_conf.pop('arg1')
    expected_conf['arg5'] = conf['5']

    result = root_config_parser_with_mandatory_and_optional_arguments.normalize_configuration(conf=conf)

    assert result == expected_conf


def test_normalize_config_dict_select_long_names_for_every_argument_in_config_with_subgroups_for_root_config_parser(
        root_config_parser_with_subgroups):
    """
    Test that every argument in a configuration has at the end its long name after the normalization
    """
    conf_file = 'basic_configuration_with_subgroups.json'
    conf = load_configuration_from_json_file(file_name=conf_file)
    expected_conf = load_configuration_from_json_file(file_name=conf_file)
    expected_conf['argument1'] = expected_conf.pop('arg1')
    expected_conf['argument3'] = expected_conf.pop('arg3')
    expected_conf['arg5'] = expected_conf.pop('5')
    expected_conf['g2']['g2_sg1']['a4'] = expected_conf['g2']['g2_sg1'].pop('a4')

    result = root_config_parser_with_subgroups.normalize_configuration(conf=conf)

    assert result == expected_conf


def test_parse_config_environment_variables_return_correct_configuration(root_config_parser_with_subgroups):
    """
    Test that the parsing of environment variables works correctly
    """
    conf_file = 'basic_configuration_with_subgroups.json'

    created_environment_variables = define_environment_variables_configuration_from_json_file(
        file_name=conf_file,
        simple_argument_prefix=root_config_parser_with_subgroups.simple_arguments_prefix[0],
        group_arguments_prefix=root_config_parser_with_subgroups.get_groups_prefixes())

    expected_conf = load_configuration_from_json_file(file_name=conf_file)

    expected_conf['g1']['g1-sg1'] = {}
    expected_conf['g1']['g1-sg2'] = {}
    expected_conf['g2']['g2-sg1'] = {}
    g1_sg1 = expected_conf['g1'].pop('g1_sg1')
    g1_sg2 = expected_conf['g1'].pop('g1_sg2')
    g2_sg1 = expected_conf['g2'].pop('g2_sg1')

    expected_conf['g1']['g1-sg1']['a1'] = str(g1_sg1['a1'])
    expected_conf['g1']['g1-sg1']['a2'] = bool(g1_sg1['a2'])
    expected_conf['g1']['g1-sg1']['a3'] = str(g1_sg1['a3'])
    expected_conf['g1']['g1-sg1']['type'] = str(g1_sg1['type'])

    expected_conf['g1']['g1-sg2']['a1'] = str(g1_sg2['a1'])
    expected_conf['g1']['g1-sg2']['a2'] = g1_sg2['a2']
    expected_conf['g1']['g1-sg2']['a3'] = g1_sg2['a3']
    expected_conf['g1']['g1-sg2']['type'] = g1_sg2['type']

    expected_conf['argument1'] = expected_conf.pop('arg1')
    expected_conf['argument3'] = expected_conf.pop('arg3')
    expected_conf['arg5'] = expected_conf.pop('5')

    expected_conf['g2']['g2-sg1']['a1'] = float(g2_sg1['a1'])
    expected_conf['g2']['g2-sg1']['a3'] = g2_sg1['a3']
    expected_conf['g2']['g2-sg1']['a4'] = g2_sg1['a4']
    expected_conf['g2']['g2-sg1']['type'] = g2_sg1['type']

    result = root_config_parser_with_subgroups.parse_config_environment_variables()

    assert result == expected_conf

    remove_environment_variables_configuration(variables_names=created_environment_variables)


def test_parse_config_environment_variables_with_wrong_argument_raise_an_exception(
        root_config_parser_with_subgroups):
    """
    Test that the parsing of environment variables raises a BadTypeException with wrong types
    """
    conf_file = 'basic_configuration_with_subgroups_wrong_argument_type_value.json'

    created_environment_variables = define_environment_variables_configuration_from_json_file(
        file_name=conf_file,
        simple_argument_prefix=root_config_parser_with_subgroups.simple_arguments_prefix[0],
        group_arguments_prefix=root_config_parser_with_subgroups.get_groups_prefixes())

    with pytest.raises(BadTypeException):
        _ = root_config_parser_with_subgroups.parse_config_environment_variables()

    remove_environment_variables_configuration(variables_names=created_environment_variables)


def test_add_subgroup(root_config_parser_with_mandatory_and_optional_arguments):
    """
    Test that a subgroup is correctly added
    """
    assert len(root_config_parser_with_mandatory_and_optional_arguments.subgroup_parsers) == 0

    root_config_parser_with_mandatory_and_optional_arguments.add_subgroup(subgroup_type='sub')

    assert len(root_config_parser_with_mandatory_and_optional_arguments.subgroup_parsers) == 1

    root_config_parser_with_mandatory_and_optional_arguments.add_subgroup(subgroup_type='sub1')

    assert len(root_config_parser_with_mandatory_and_optional_arguments.subgroup_parsers) == 2

    root_config_parser_with_mandatory_and_optional_arguments.add_subgroup(subgroup_type='sub2')

    assert len(root_config_parser_with_mandatory_and_optional_arguments.subgroup_parsers) == 3

    root_config_parser_with_mandatory_and_optional_arguments.add_subgroup(subgroup_type='sub3')

    assert len(root_config_parser_with_mandatory_and_optional_arguments.subgroup_parsers) == 4


def test_add_repeated_subgroup_raise_an_exception(root_config_parser_with_subgroups):
    """
    Test that adding a repeated subgroup raises an AlreadyAddedSubgroupException
    """
    assert len(root_config_parser_with_subgroups.subgroup_parsers) == 2

    with pytest.raises(AlreadyAddedSubgroupException):
        root_config_parser_with_subgroups.add_subgroup(subgroup_type='g2')

    assert len(root_config_parser_with_subgroups.subgroup_parsers) == 2


def test_get_subgroups_prefix(root_config_parser_with_subgroups):
    """
    Test that all the subgroups prefixes are returned
    """
    expected_prefixes = ['TEST_G1_', 'TEST_G2_']

    result = root_config_parser_with_subgroups.get_groups_prefixes()
    assert len(result) == len(expected_prefixes)
    assert result == expected_prefixes


def test_get_longest_arguments_names(root_config_parser_with_subgroups):
    """
    Test that all the arguments of the parser are returned
    """
    expected_arguments_names = ['help', 'a', 'argument1', 'argumento2', 'argument3', 'arg4', 'arg5', 'g1', 'g2']

    result = root_config_parser_with_subgroups.get_longest_arguments_names()
    assert len(result) == len(expected_arguments_names)
    assert result == expected_arguments_names
