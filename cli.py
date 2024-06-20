from argparse import ArgumentParser, Namespace
import generator
import json
import logging
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
    parser.add_argument('--log',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='logging level to use, default: INFO'
    )
    return parser


def _load_schema(schema: str) -> dict[str, str]:
    json_string: str
    if '{' in schema: # inline schema
        logging.debug('loading inline schema...')
        json_string = schema
    else: # path to a schema file
        logging.debug(f'loading schema from a file \"{schema}\"...')
        try:
            with open(schema, 'r') as file:
                json_string = file.read()
        except FileNotFoundError:
            logging.error(f'unable to open file, not found: \"{schema}\"')
            sys.exit(1)
        except IsADirectoryError:
            logging.error(f'unable to open file, it is a directory: \"{schema}\"')
            sys.exit(1)
    logging.debug(f'attempting to parse the schema: \"{json_string}\"')
    result = json.loads(json_string)
    logging.info(f'schema loaded successfully')
    return result


def _parse_arguments(parser: ArgumentParser, args: list[str]) -> Namespace:
    namespace = parser.parse_args(args)

    match namespace.log:
        case 'DEBUG':
            logging.basicConfig(level=logging.DEBUG)

        case 'INFO':
            logging.basicConfig(level=logging.INFO)

        case 'WARNING':
            logging.basicConfig(level=logging.WARNING)

        case 'ERROR':
            logging.basicConfig(level=logging.ERROR)

    # count
    if namespace.count < 0:
        logging.error(f'argument -c/--count: invalid non-negative int value: {namespace.count}')
        sys.exit(1)
    logging.debug(f'argument -c/--count: {namespace.count}')
    
    # schema
    schema_generator: generator.SchemaGenerator
    try:
        schema = _load_schema(namespace.schema)
        schema_generator = generator.SchemaGenerator(schema)
    except ValueError:
        logging.error(f'argument -s/--schema: invalid schema')
        sys.exit(1)
    namespace.generator = schema_generator
    
    # lines
    if namespace.lines <= 0:
        logging.error(f'argument -l/--lines: invalid positive int value: {namespace.lines}')
        sys.exit(1)
    logging.debug(f'argument -l/--lines: {namespace.lines}')
    
    # processes
    if namespace.processes <= 0:
        logging.error(f'argument -p/--processes: invalid positive int value: {namespace.processes}')
        sys.exit(1)
    cpu_count = os.cpu_count()
    if namespace.processes > cpu_count:
        logging.warning(f'argument -p/--processes ({namespace.processes}) is larger than the amount of CPUs ({cpu_count}), overriding the argument')
        namespace.processes = cpu_count
    logging.debug(f'argument -p/--processes: {namespace.processes}')

    return namespace


def get_arguments() -> Namespace:
    parser = _create_parser()
    namespace = _parse_arguments(parser, sys.argv[1:])
    return namespace


ARG_FILE = ['-f', 'file']
ARG_SCHEMA = ['-s', '{\"age\":\"int:rand(1, 100)\"}']
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

    (ARG_FILE + ['-s', '{\"age\":\"int:rand(1, 100)\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:10\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:aaa\"}'], False),
    (ARG_FILE + ['-s', '{\"age\":\"int:[1,50,100]\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:[1,???,100]\"}'], False),
    (ARG_FILE + ['-s', '{\"age\":\"str:rand(1, 100)\"}'], False),

    (ARG_FILE + ['-s', '{\"name\":\"str:[\'John\',\'Adam\']\"}'], True),
    (ARG_FILE + ['-s', '{\"name\":\"str:[\"John\",\"Adam\"]\"}'], False),

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
