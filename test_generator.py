from datetime import datetime
import generator as gr
import pytest
import re


@pytest.mark.freeze_time('2021-10-07')
def test_timestamp_generator():
    expected_timestamp = datetime(2021, 10, 7).timestamp()
    generator = gr.TimestampGenerator()
    assert generator.get() == expected_timestamp


@pytest.mark.parametrize('args,output', [
    (['int'], None),
    (['str'], ''),
    (['int', 10], 10),
    (['str', 'aaa'], 'aaa')
])
def test_const_generator(args, output):
    generator = gr.ConstGenerator(*args)
    for _ in range(5):
        assert generator.get() == output


@pytest.mark.parametrize('args,min,max', [
    ([1, 6], 1, 6),
    ([], gr.RangeGenerator.DEFAULT_MIN, gr.RangeGenerator.DEFAULT_MAX)
])
def test_range_generator(args, min, max):
    generator = gr.RangeGenerator(*args)
    for _ in range(50):
        value = generator.get()
        assert value >= min
        assert value <= max


@pytest.mark.parametrize('values', [
    ([1, 2, 3]),
    (['a', 'b', 'c'])
])
def test_list_generator(values):
    generator = gr.ListGenerator(values)
    for _ in range(50):
        assert generator.get() in values


def test_random_str_generator():
    generator = gr.RandomStrGenerator()
    for _ in range(5):
        uuid_str = generator.get()
        assert re.match(
            r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}',
            uuid_str
        )


@pytest.mark.parametrize('type,value,is_valid,generator_class,generator_args', [
    ('timestamp', '', True, gr.TimestampGenerator, []),
    ('timestamp', 'rand', False, None, None),

    ('str', 'rand', True, gr.RandomStrGenerator, []),
    ('str', "['a', 'b', 'c']", True, gr.ListGenerator, [['a', 'b', 'c']]),
    ('str', "['a','b','c']", True, gr.ListGenerator, [['a', 'b', 'c']]),
    ('str', "['a','b',3]", False, None, None),
    ('str', "[1,2,3]", False, None, None),
    ('str', 'rand(1, 20)', False, None, None),
    ('str', 'cat', True, gr.ConstGenerator, ['str', 'cat']),

    ('int', 'rand', True, gr.RangeGenerator, []),
    ('int', "[1, 2, 3]", True, gr.ListGenerator, [[1, 2, 3]]),
    ('int', "[1,2,3]", True, gr.ListGenerator, [[1, 2, 3]]),
    ('int', "[1,2,'c']", False, None, None),
    ('int', "['a','b','c']", False, None, None),
    ('int', 'rand(1, 20)', True, gr.RangeGenerator, [1, 20]),
    ('int', 'rand(1,20)', True, gr.RangeGenerator, [1, 20]),
    ('int', '10', True, gr.ConstGenerator, ['int', 10]),
    ('int', 'cat', False, None, None),
])
def test_create_generator(type, value, is_valid, generator_class, generator_args):
    if is_valid:
        generator = generator_class(*generator_args)
        assert gr.create_generator(type, value) == generator
    else:
        with pytest.raises(ValueError):
            gr.create_generator(type, value)
