from argparse import ArgumentParser, Namespace
import generator
import json
import os
import sys


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
        help='base file name, when generating multiplie files it will be expanded by an affix, do not specify the extension',
        required=True
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
    return json.loads(json_string)


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
