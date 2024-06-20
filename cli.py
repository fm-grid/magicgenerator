from argparse import ArgumentParser, Namespace
import configparser
import generator
import json
import logging
import os
import sys


CONFIG_FILE = 'config.ini'


def _create_parser() -> ArgumentParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'DEFAULT' not in config:
        logging.error('no config file found')
        sys.exit(1)
    default_config = config['DEFAULT']

    parser = ArgumentParser(
        prog='magicgenerator',
        description='This is a console utility that can generate random test data in the JSON lines format based on provided data schema.'
    )
    parser.add_argument(  # output
        '-o',
        '--output',
        type=str,
        default=default_config['output'],
        help=f'directory to which all generated files will be saved, default: {default_config['output']}'
    )
    parser.add_argument(  # count
        '-c',
        '--count',
        type=int,
        default=int(default_config['count']),
        help=f'number of json files to generate, default: {int(default_config['count'])}'
    )
    parser.add_argument(  # filename
        '-f',
        '--filename',
        type=str,
        default=default_config['filename'],
        help=f'base file name (default: \"{default_config['filename']}\"), when generating multiplie files it will be expanded by an affix, do not specify the extension'
    )
    parser.add_argument(  # affix
        '-a',
        '--affix',
        choices=['count', 'random', 'uuid'],
        default=default_config['affix'],
        help=f'file name affix, required when generating multiple files, default: {default_config['affix']}'
    )
    parser.add_argument(  # schema
        '-s',
        '--schema',
        type=str,
        help='inline json schema or path to a file containing one',
        required=True
    )
    parser.add_argument(  # lines
        '-l',
        '--lines',
        type=int,
        default=int(default_config['lines']),
        help=f'number of lines each json file will contain, default: {int(default_config['lines'])}'
    )
    parser.add_argument(  # clear-path
        '--clear-path',
        action='store_true',
        help='clear the directory of all the files with the same base file name before generating new ones'
    )
    parser.add_argument(  # processes
        '-p',
        '--processes',
        type=int,
        default=int(default_config['processes']),
        help=f'number of processes that will be used to generate files, default: {int(default_config['processes'])}'
    )
    parser.add_argument(  # log
        '--log',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=default_config['log'],
        help=f'logging level to use, default: {default_config['log']}'
    )
    return parser


def _load_schema(schema: str) -> dict[str, str]:
    json_string: str
    if '{' in schema:  # inline schema
        logging.debug('loading inline schema...')
        json_string = schema
    else:  # path to a schema file
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
    logging.info('schema loaded successfully')
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
        logging.error('argument -s/--schema: invalid schema')
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
