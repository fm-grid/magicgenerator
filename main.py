from argparse import ArgumentParser, Namespace
import sys

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
        help='base file name, when generating multiplie files it will be expanded by an affix',
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


def parse_arguments(parser: ArgumentParser, args: list[str]) -> Namespace:
    namespace = parser.parse_args(args)
    print(namespace)
    ...

def main():
    parser = create_parser()
    namespace = parse_arguments(parser, sys.argv[1:])


if __name__ == '__main__':
    main()
