from argparse import Namespace
import cli
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
import random
import uuid


def _generate_affixes(type: str, count: int) -> list[str]:
    if count < 1:
        raise ValueError

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
        case _:
            raise ValueError


def _list_split(list: list, n: int) -> list[list]:
    sublists = [[] for _ in range(n)]
    for index, item in enumerate(list):
        sublists[index % n].append(item)
    return sublists


def _generate_line(namespace: Namespace) -> str:
    data = namespace.generator.get()
    line = json.dumps(data)
    return line


def _generate_lines(namespace: Namespace, lines: int = None) -> list[str]:
    if lines is None:
        lines = namespace.lines
    return [_generate_line(namespace) for _ in range(lines)]


def _generate_file(namespace: Namespace, affix: str) -> None:
    filename = namespace.filename + affix + '.jsonl'
    path = namespace.output + '/' + filename
    try:
        with open(path, 'w') as file:
            file.write('\n'.join(_generate_lines(namespace)))
            logging.info(f'generated file: \"{path}\"')
    except OSError:
        logging.error(f'unable to create file: \"{path}\"')


def _generate_files(namespace: Namespace, affixes: list[str]) -> None:
    for affix in affixes:
        _generate_file(namespace, affix)


def _generate_files_multithreaded(namespace: Namespace, affixes: list[str], threads: int = None) -> None:
    if threads is None:
        threads = namespace.processes
    affix_lists = _list_split(affixes, threads)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        def func(affixes):
            _generate_files(namespace, affixes)
        executor.map(func, affix_lists)


def _main_stdout(namespace: Namespace) -> None:
    for _ in range(namespace.lines):
        print(_generate_line(namespace))


def _prepare_dir(namespace: Namespace) -> None:
    if not os.path.exists(namespace.output):
        logging.info('directory does not exist, creating it')
        os.mkdir(namespace.output)

    if namespace.clear_path:
        logging.info('clearing the directory (--clear-path argument)')
        deleted_files = 0
        for file in os.listdir(namespace.output):
            path = os.path.join(namespace.output, file)
            if not os.path.isfile(path):
                continue
            if not str(file).startswith(namespace.filename):
                continue
            os.remove(path)
            deleted_files += 1
        logging.info(f'deleted {deleted_files} file(s)')


def _main_generate_files(namespace: Namespace) -> None:
    _prepare_dir(namespace)
    affixes = _generate_affixes(namespace.affix, namespace.count)
    if len(affixes) > 1:
        _generate_files_multithreaded(namespace, affixes)
    else:
        _generate_file(namespace, '')


def main():
    namespace = cli.get_arguments()

    match namespace.count:
        case 0:
            _main_stdout(namespace)

        case _:
            _main_generate_files(namespace)


if __name__ == '__main__':
    main()
