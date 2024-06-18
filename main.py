from argparse import ArgumentParser, Namespace
from concurrent.futures import ThreadPoolExecutor
import generator
import json
import os
import random
import sys
import uuid


def create_parser() -> ArgumentParser:
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


def load_schema(schema: str) -> dict[str, str]:
    json_string: str
    if '{' in schema: # inline schema
        json_string = schema
    else: # path to a schema file
        with open(schema, 'r') as file:
            json_string = file.read()
    return json.loads(json_string)


def parse_arguments(parser: ArgumentParser, args: list[str]) -> Namespace:
    namespace = parser.parse_args(args)

    # count
    if namespace.count < 0:
        parser.error(f'argument -c/--count: invalid non-negative int value: {namespace.count}')
    
    # schema
    schema_generator: generator.SchemaGenerator
    try:
        schema = load_schema(namespace.schema)
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


def generate_affixes(type: str, count: int) -> list[str]:
    match type:
        case 'count':
            digits = len(str(count - 1))
            return [f'{i:0{digits}d}' for i in range(count)]
    
        case 'random':
            values = set()
            while len(values) < count:
                values.add(random.randbytes(16).hex())
            return list(values)
        
        case 'uuid':
            values = set()
            while len(values) < count:
                values.add(str(uuid.uuid4()))
            return list(values)


def list_split(list: list, n: int) -> list[list]:
    sublists = [[] for _ in range(n)]
    for index, item in enumerate(list):
        sublists[index % n].append(item)
    return sublists


def generate_line(namespace: Namespace) -> str:
    data = namespace.generator.get()
    line = json.dumps(data)
    return line


def generate_lines(namespace: Namespace, lines: int = None) -> list[str]:
    if lines is None:
        lines = namespace.lines
    return [generate_line(namespace) for _ in range(lines)]


def generate_file(namespace: Namespace, affix: str):
    filename = namespace.filename + affix + '.jsonl'
    path = namespace.output + '/' + filename
    with open(path, 'w') as file:
        file.write('\n'.join(generate_lines(namespace)))


def generate_files(namespace: Namespace, affixes: list[str]):
    for affix in affixes:
        generate_file(namespace, affix)


def main_stdout(namespace: Namespace):
    for _ in range(namespace.lines):
        print(generate_line(namespace))

def main_generate_files(namespace: Namespace):
    if not os.path.exists(namespace.output):
        os.mkdir(namespace.output)
    affixes = generate_affixes(namespace.affix, namespace.count)
    affix_lists = list_split(affixes, namespace.processes)
    with ThreadPoolExecutor(max_workers=namespace.processes) as executor:
        func = lambda affixes: generate_files(namespace, affixes)
        executor.map(func, affix_lists)


def main():
    parser = create_parser()
    namespace = parse_arguments(parser, sys.argv[1:])

    match namespace.count:
        case 0:
            main_stdout(namespace)

        case _:
            main_generate_files(namespace)


if __name__ == '__main__':
    main()
