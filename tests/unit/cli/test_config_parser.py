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
    BadContextException, MissingValueException, SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, \
    NoNameSpecifiedForSubgroupException, TooManyArgumentNamesException, MissingArgumentException

from tests.utils.cli.base_config_parser import load_configuration_from_json_file, \
    generate_list_of_tuples_of_configuration_from_json_file


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
    parser.add_argument(name_arg_a_1, longest_name_arg_a, name_arg_a_2, is_mandatory=expected_argument_a.is_mandatory, is_flag=expected_argument_a.is_flag,
                        argument_type=expected_argument_a.type, help_text=expected_argument_a.help_text,
                        default_value=expected_argument_a.default_value)

    parser.add_argument(name_arg_xx_1, longest_name_arg_xx, name_arg_xx_2, is_mandatory=expected_argument_xx.is_mandatory, is_flag=expected_argument_xx.is_flag,
                        argument_type=expected_argument_xx.type, help_text=expected_argument_xx.help_text,
                        default_value=expected_argument_xx.default_value)

    arguments = parser.get_arguments()

    assert len(arguments) == 6

    assert longest_name_arg_a in arguments.keys()

    assert longest_name_arg_xx in arguments.keys()

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


def test_validate_accepts_configuration_when_no_mandatory_arguments_exist(base_config_parser_no_mandatory_arguments):
    """
    Test if a configuration passes the validation if there is no mandatory argument
    """
    conf = load_configuration_from_json_file('basic_configuration_without_mandatory_arguments.json')

    try:
        validated_config = base_config_parser_no_mandatory_arguments.validate(conf)
        assert validated_config == conf

    except MissingArgumentException:
        assert False


def test_validate_adds_defaults_for_no_arguments_defined_in_configuration_that_have_one(base_config_parser):
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

    args = generate_list_of_tuples_of_configuration_from_json_file('basic_configuration.json')
    acc = {}

    expected_acc = {'argumento1': 5,
                    "argumento2": "this a mandatory argument",
                    "argument3": False,
                    "dded": 10.5}

    args, acc = base_config_parser._parse(args, acc)

    assert not args
    assert acc == expected_acc


def test_parser_raise_an_exception_with_an_unkown_argument(base_config_parser):

    """
    Test that the _parser method return correct values for different arguments in configuration
    """

    args = generate_list_of_tuples_of_configuration_from_json_file('basic_configuration.json')
    args.append(('unknown_arg', 'This is a new argument'))
    acc = {}

    with pytest.raises(NotImplementedError):
        _, _ = base_config_parser._parse(args, acc)

#####################
# ROOT PARSER TESTS #
#####################
# Test add_argument optargs #


def test_add_argument_short():
    """
    Test if a short argument is added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a')
    assert parser.short_arg == 'a:'


def test_add_argument_flag():
    """
    Add a short flag to the parser

    Test if the argument was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'


def test_add_argument_2_short():
    """
    Add two short argument (an argument and a flag) to the parser

    Test if the arguments was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'
    parser.add_argument('b')
    assert parser.short_arg == 'ab:'


def test_add_argument_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa')
    assert parser.long_arg == ['aaa=']


def test_add_flag_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa', is_flag=True)
    assert parser.long_arg == ['aaa']


# full parsing test #
def check_parsing_result(parser, input_str, outputs):
    """
    Check that input_str is correctly parsed by parser
    """
    result = parser.parse(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_empty_parser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : UnknownArgException(a)
    - "-a --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    Parser description :

    - base parser arguments : None
    - subparser toto bound to the argument sub with sub arguments : None
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


def test_main_parser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknownArgException(sub)
    - "-b" : UnknownArgException(b)

    Parser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : None
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


def test_actor_subparser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    Parser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : -b and --name
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', is_flag=True, action=store_true)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

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


def test_create_two_component():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub toto -b --name tutu',
                         {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}})


def test_create_two_with_different_type_component():
    """
    Create two component with different type with the following cli :
    --sub toto --name titi --sub tutu --name tete

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParser('tutu')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub tutu --name tete',
                         {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}}})


def test_create_component_that_already_exist():
    """
    Create two component with the same name with the following cli
    --sub toto --name titi --sub toto --name titi

    test if an ComponentAlreadyExistException is raised
    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    with pytest.raises(SubgroupAlreadyExistException):
        check_parsing_result(parser, '--sub toto --name titi --sub toto --name titi', None)


def test_argument_with_val():
    """
    test to parse strings with a parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    Parser description :

    - base parser arguments : -c (not flag)
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c')

    with pytest.raises(MissingValueException):
        check_parsing_result(parser, '-c', None)

    check_parsing_result(parser, '-c 1', {'c': '1'})


# multi name tests #
def test_short_and_long_name_val():
    """
    Add an argument to a parser with two name long and short and test if the
    value is only bind to the long name in the parsing result

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c', 'coco')

    check_parsing_result(parser, '-c 1', {'coco': '1'})


def test_add_two_short_name():
    """
    Add an argument to a parser with two short name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParser(help_arg=False)
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('c', 'd')


def test_add_two_long_name():
    """
    Add an argument to a parser with two long name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParser(help_arg=False)
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('coco', 'dodo')


# Type tests #
def test_default_type():
    """
    add an argument without specifying the type it must catch. Parse a string
    that contains only this argument and test if the value contained in the
    result is a string

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a')
    result = parser.parse('-a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], str)


def test_other_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument and test if the value contained in the result is
    an int

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', argument_type=int)
    result = parser.parse('-a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)


def test_cant_convert_to_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument with a value that is not an int test if an
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', argument_type=int)

    with pytest.raises(BadTypeException):
        parser.parse('-a a'.split())


# parse with ComponentSubparser tests #
def test_add_actor_subparser_that_already_exists():
    """
    Add a component_subparser that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('toto', subparser)
    subparser2 = SubgroupConfigParser('titi')
    subparser2.add_argument('n', 'name')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_subgroup_parser('toto', subparser2)


def test_add_actor_subparser_with_two_name():
    """
    add a component subparser with one short name and one long name
    parse a string and test if the value is only bind to the long name
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('a', 'aaa', is_flag=True, action=store_true, default_value=False)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)
    check_parsing_result(parser, '--sub titi -a --name tutu', {'sub': {'tutu': {'aaa': True, 'type': 'titi'}}})


def test_add_component_subparser_that_already_exists2():
    """
    Add a component_subparser with no argument 'name'
    test if a SubParserWithoutNameArgumentException is raised
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')

    with pytest.raises(SubgroupParserWithoutNameArgumentException):
        parser.add_subgroup_parser('toto', subparser)


def test_parse_empty_string_default_value():
    """
    Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', default_value=1)
    result = parser.parse(''.split())
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1


############################
# COMPONENT_SUBPARSER TEST #
############################
def test_component_subparser_empty(subgroup_parser):
    """
    Test component_subparser, parse an empty token list.
    Must return an empty dictionary as parse result and an empty token
    list
    """
    assert subgroup_parser.parse([]) == ([], {})


def test_component_subparser_normal_token_list(subgroup_parser):
    """
    test component_subparser, parse a token list which contain only subparser
    argument [('a', '')].

    must return return a  dictionary {'a':''} as parse result
    and an empty token list

    """
    assert subgroup_parser.parse([('a', '')]) == ([], {'a': None})


def test_component_subparser_full_token_list(subgroup_parser):
    """
    test component_subparser, parse a token list which contain subparser
    argument and arguments from other parser[('a', ''), ('b', '')].

    must return return a  dictionary {'a':''} as parse result
    and a token list that contains the unparsed arguments : [('b', '')].

    """
    assert subgroup_parser.parse([('a', ''), ('b', '')]) == ([('b', '')],
                                                             {'a': None})


def test_subparser_empty_token_list_default_value():
    """
    Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('a', default_value=1)
    acc, result = subparser.parse([])
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1
    assert acc == []
