from argparse import Namespace
import magicgenerator
import os
import pytest
from unittest.mock import patch


@pytest.mark.parametrize('type,count,is_valid', [
    ('count', 10, True),
    ('random', 25, True),
    ('uuid', 5, True),
    ('rand', 10, False),
    ('count', -10, False)
])
def test_generate_affixes(type, count, is_valid):
    if is_valid:
        affixes = magicgenerator._generate_affixes(type, count)
        assert len(affixes) == count
    else:
        with pytest.raises(ValueError):
            magicgenerator._generate_affixes(type, count)


@pytest.mark.parametrize('list,parts', [
    ([1, 2, 3, 4, 5, 6, 7, 8], 2),
    ([1, 2, 3, 4, 5, 6, 7, 8], 3),
    ([1, 2, 3, 4, 5, 6, 7, 8], 5),
    ([1, 2, 3, 4, 5, 6, 7, 8], 6)
])
def test_list_split(list, parts):
    lists = magicgenerator._list_split(list, parts)
    lengths = {len(l) for l in lists}
    assert (max(lengths) - min(lengths)) <= 1


BASE_FILENAME_FILES = 3
UNRELATED_FILES = 3
@pytest.fixture
def example_dir(tmp_path):
    (tmp_path / 'file1.jsonl').write_text('{}')
    (tmp_path / 'file2.jsonl').write_text('{}')
    (tmp_path / 'file3.jsonl').write_text('{}')
    (tmp_path / 'unrelated1.txt').write_text('aaa')
    (tmp_path / 'unrelated2.txt').write_text('bbb')
    (tmp_path / 'schema.json').write_text('{\"name\":\"str:[\'John\',\'Adam\']\"}')
    return tmp_path


@pytest.mark.parametrize('args,count', [
    (['-c', '10'], 10),
    (['-c', '100', '-p', '4'], 100)
])
def test_generate_file(example_dir, args, count):
    full_args = [''] + args + [
        '-s', str(example_dir / 'schema.json'),
        '-o', str(example_dir),
        '--clear-path'
    ]
    with patch('sys.argv', full_args):
        assert len(os.listdir(example_dir)) == BASE_FILENAME_FILES + UNRELATED_FILES
        magicgenerator.main()
        assert len(os.listdir(example_dir)) == count + UNRELATED_FILES


def test_prepare_dir(example_dir):
    assert len(os.listdir(example_dir)) == BASE_FILENAME_FILES + UNRELATED_FILES
    namespace = Namespace(
        output=str(example_dir),
        filename='file',
        clear_path=True
    )
    magicgenerator._prepare_dir(namespace)
    assert len(os.listdir(example_dir)) == UNRELATED_FILES
