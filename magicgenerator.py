from argparse import Namespace
import cli
from concurrent.futures import ThreadPoolExecutor
import json
import os
import random
import uuid


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


def generate_file(namespace: Namespace, affix: str) -> None:
    filename = namespace.filename + affix + '.jsonl'
    path = namespace.output + '/' + filename
    with open(path, 'w') as file:
        file.write('\n'.join(generate_lines(namespace)))


def generate_files(namespace: Namespace, affixes: list[str]) -> None:
    for affix in affixes:
        generate_file(namespace, affix)


def generate_files_multithreaded(namespace: Namespace, affixes: list[str], threads: int = None) -> None:
    if threads is None:
        threads = namespace.processes
    affix_lists = list_split(affixes, threads)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        func = lambda affixes: generate_files(namespace, affixes)
        executor.map(func, affix_lists)


def main_stdout(namespace: Namespace) -> None:
    for _ in range(namespace.lines):
        print(generate_line(namespace))


def prepare_dir(namespace: Namespace) -> None:
    if not os.path.exists(namespace.output):
        os.mkdir(namespace.output)
    
    if namespace.clear_path:
        for file in os.listdir(namespace.output):
            path = os.path.join(namespace.output, file)
            if not os.path.isfile(path):
                continue
            if not str(file).startswith(namespace.filename):
                continue
            os.remove(path)


def main_generate_files(namespace: Namespace) -> None:
    prepare_dir(namespace)
    affixes = generate_affixes(namespace.affix, namespace.count)
    generate_files_multithreaded(namespace, affixes)


def main():
    namespace = cli.get_arguments()

    match namespace.count:
        case 0:
            main_stdout(namespace)

        case _:
            main_generate_files(namespace)


if __name__ == '__main__':
    main()
