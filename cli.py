from argparse import ArgumentParser, Namespace
import generator
import json
import os
import pytest
import sys
from unittest.mock import patch


def _create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output',
        type=str,
        default='.',
        help='directory to which all generated files will be saved, default: current working directory'
    )
    parser.add_argument('-c', '--count',
        type=int,
        default=1,
        help='number of json files to generate, default: 1'
    )
    parser.add_argument('-f', '--filename',
        type=str,
        default='file',
        help='base file name (default: \'file\'), when generating multiplie files it will be expanded by an affix, do not specify the extension'
    )
    parser.add_argument('-a', '--affix',
        choices=['count', 'random', 'uuid'],
        default='count',
        help='file name affix, required when generating multiple files, options: count (default), random, uuid'
    )
    parser.add_argument('-s', '--schema',
        type=str,
        help='inline json schema or path to a file containing one',
        required=True
    )
    parser.add_argument('-l', '--lines',
        type=int,
        default=1000,
        help='number of lines each json file will contain, default: 1000'
    )
    parser.add_argument('--clear-path',
        action='store_true',
        help='clear the directory of all the files with the same base file name before generating new ones'
    )
    parser.add_argument('-p', '--processes',
        type=int,
        default=1,
        help='number of processes that will be used to generate files'
    )
    return parser


def _load_schema(schema: str) -> dict[str, str]:
    json_string: str
    if '{' in schema: # inline schema
        json_string = schema
    else: # path to a schema file
        with open(schema, 'r') as file:
            json_string = file.read()
    return json.loads(json_string.replace('\'', '\"'))


def _parse_arguments(parser: ArgumentParser, args: list[str]) -> Namespace:
    namespace = parser.parse_args(args)

    # count
    if namespace.count < 0:
        parser.error(f'argument -c/--count: invalid non-negative int value: {namespace.count}')
    
    # schema
    schema_generator: generator.SchemaGenerator
    try:
        schema = _load_schema(namespace.schema)
        schema_generator = generator.SchemaGenerator(schema)
    except ValueError:
        parser.error(f'argument -s/--schema: invalid schema')
    namespace.generator = schema_generator
    
    # lines
    if namespace.lines <= 0:
        parser.error(f'argument -l/--lines: invalid positive int value: {namespace.lines}')
    
    # processes
    if namespace.processes <= 0:
        parser.error(f'argument -p/--processes: invalid positive int value: {namespace.processes}')
    namespace.processes = min(namespace.processes, os.cpu_count())
    
    return namespace


def get_arguments() -> Namespace:
    parser = _create_parser()
    namespace = _parse_arguments(parser, sys.argv[1:])
    return namespace


ARG_FILE = ['-f', 'file']
ARG_SCHEMA = ['-s', "{'age':'int:rand(1, 100)'}"]
ARGS = ARG_FILE + ARG_SCHEMA
@pytest.mark.parametrize('args,is_valid', [
    (ARG_FILE + ARG_SCHEMA, True),

    (ARGS + ['-c', '10'], True),
    (ARGS + ['-c', '0'], True),
    (ARGS + ['-c', '-10'], False),

    (ARGS + ['-a', 'count'], True),
    (ARGS + ['-a', 'random'], True),
    (ARGS + ['-a', 'uuid'], True),
    (ARGS + ['-a', 'rand'], False),
    (ARGS + ['-a', 'aaa'], False),

    (ARG_FILE + ['-s', "{'age':'int:rand(1, 100)'}"], True),
    (ARG_FILE + ['-s', "{'age':'int:'}"], True),
    (ARG_FILE + ['-s', "{'age':'int:10'}"], True),
    (ARG_FILE + ['-s', "{'age':'int:aaa'}"], False),
    (ARG_FILE + ['-s', "{'age':'int:[1,50,100]'}"], True),
    (ARG_FILE + ['-s', "{'age':'int:[1,???,100]'}"], False),

    (ARG_FILE + ['-s', "{'age':'str:rand(1, 100)'}"], False),

    (ARGS + ['-l', '1000'], True),
    (ARGS + ['-l', '0'], False),
    (ARGS + ['-l', '-1000'], False),

    (ARGS + ['-p', '-10'], False),
    (ARGS + ['-p', '1'], True),
    (ARGS + ['-p', '999'], True)
])
def test_get_arguments(args, is_valid):
    with patch('sys.argv', [''] + args):
        if is_valid:
            get_arguments()
        else:
            with pytest.raises(SystemExit):
                get_arguments()


if __name__ == '__main__':
    pytest.main([__file__])
