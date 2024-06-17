from datetime import datetime
import json
import pytest
import random
import re
import uuid


class Generator:

    def __init__(self):
        raise ValueError
    
    def get(self):
        raise ValueError
    
    def __eq__(self, other):
        same_class = self.__class__.__name__ == other.__class__.__name__
        same_values = self.__dict__ == other.__dict__
        return same_class and same_values


class TimestampGenerator(Generator):

    def __init__(self):
        pass
    
    def get(self):
        return datetime.timestamp(datetime.now())
    

class ConstGenerator(Generator):

    DEFAULT_CONST_STR = ''
    DEFAULT_CONST_INT = None

    def __init__(self, type: str, value=None):
        if type not in ['str', 'int']:
            raise ValueError
        match (type, value):
            case ('str', None):
                self.value = ConstGenerator.DEFAULT_CONST_STR
            case ('int', None):
                self.value = ConstGenerator.DEFAULT_CONST_INT
            case (_, None):
                raise ValueError
            case ('str', v):
                if not isinstance(v, str):
                    raise ValueError
                self.value = v
            case ('int', v):
                if not isinstance(v, int):
                    raise ValueError
                self.value = v
    
    def get(self):
        return self.value


class RangeGenerator(Generator):

    DEFAULT_MIN = 0
    DEFAULT_MAX = 10_000

    def __init__(self, min: int = DEFAULT_MIN, max: int = DEFAULT_MAX):
        self.min = min
        self.max = max
    
    def get(self):
        return random.randint(self.min, self.max)


class ListGenerator(Generator):
    
    def __init__(self, values: list[str] | list[int]):
        if len(values) < 1:
            raise ValueError
        is_strs = True
        is_ints = True
        for value in values:
            if not isinstance(value, str):
                is_strs = False
            if not isinstance(value, int):
                is_ints = False
        if not (is_strs or is_ints):
            raise ValueError
        self.values = set(values)
    
    def get(self):
        return random.choice(list(self.values))


class RandomStrGenerator(Generator):
    
    def __init__(self):
        pass
    
    def get(self):
        return str(uuid.uuid4())


def _create_str_generator(value: str) -> Generator:
    match value:
        case '':
            return ConstGenerator('str')

        case 'rand':
            return RandomStrGenerator()

        case _ if value.startswith('rand'):
            raise ValueError
        
        case _ if value.startswith('[') and value.endswith(']'):
            value = value.replace('\'', '\"')
            values = json.loads(value)
            if not isinstance(values, list):
                raise ValueError
            for v in values:
                if not isinstance(v, str):
                    raise ValueError
            return ListGenerator(values)
        
        case _ if isinstance(value, str):
            return ConstGenerator('str', value)
        
        case _:
            raise ValueError


def _create_int_generator(value: str) -> Generator:
    match value:
        case '':
            return ConstGenerator('int')
        
        case 'rand':
            return RangeGenerator()

        case value if value.startswith('rand'):
            match = re.match(r'rand\((\d+), ?(\d+)\)', value)
            if match is None:
                raise ValueError
            min = int(match.group(1))
            max = int(match.group(2))
            return RangeGenerator(min, max)
        
        case _ if value.startswith('[') and value.endswith(']'):
            values = json.loads(value)
            if not isinstance(values, list):
                raise ValueError
            for v in values:
                if not isinstance(v, int):
                    raise ValueError
            return ListGenerator(values)
        
        case _ if isinstance(value, str):
            try:
                value = int(value)
            except:
                raise ValueError
            return ConstGenerator('int', value)
        
        case _:
            raise ValueError


def create_generator(type: str, value: str) -> Generator:
    match type:
        case 'timestamp':
            if value != '':
                raise ValueError
            return TimestampGenerator()
        
        case 'str':
            return _create_str_generator(value)

        case 'int':
            return _create_int_generator(value)

        case _:
            raise ValueError


@pytest.mark.freeze_time('2021-10-07')
def test_timestamp_generator():
    expected_timestamp = datetime(2021, 10, 7).timestamp()
    generator = TimestampGenerator()
    assert generator.get() == expected_timestamp


@pytest.mark.parametrize('args,output', [
    (['int'],None),
    (['str'],''),
    (['int', 10], 10),
    (['str', 'aaa'], 'aaa')
])
def test_const_generator(args, output):
    generator = ConstGenerator(*args)
    for _ in range(5):
        assert generator.get() == output


@pytest.mark.parametrize('args,min,max', [
    ([1, 6], 1, 6),
    ([], RangeGenerator.DEFAULT_MIN, RangeGenerator.DEFAULT_MAX)
])
def test_range_generator(args, min, max):
    generator = RangeGenerator(*args)
    for _ in range(50):
        value = generator.get()
        assert value >= min
        assert value <= max


@pytest.mark.parametrize('values', [
    ([1, 2, 3]),
    (['a', 'b', 'c'])
])
def test_list_generator(values):
    generator = ListGenerator(values)
    for _ in range(50):
        assert generator.get() in values


def test_random_str_generator():
    generator = RandomStrGenerator()
    for _ in range(5):
        uuid_str = generator.get()
        assert re.match(
            r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}',
            uuid_str
        )


@pytest.mark.parametrize('type,value,is_valid,generator_class,generator_args', [
    ('timestamp', '', True, TimestampGenerator, []),
    ('timestamp', 'rand', False, None, None),

    ('str', 'rand', True, RandomStrGenerator, []),
    ('str', "['a', 'b', 'c']", True, ListGenerator, [['a', 'b', 'c']]),
    ('str', "['a','b','c']", True, ListGenerator, [['a', 'b', 'c']]),
    ('str', "['a','b',3]", False, None, None),
    ('str', "[1,2,3]", False, None, None),
    ('str', 'rand(1, 20)', False, None, None),
    ('str', 'cat', True, ConstGenerator, ['str', 'cat']),

    ('int', 'rand', True, RangeGenerator, []),
    ('int', "[1, 2, 3]", True, ListGenerator, [[1, 2, 3]]),
    ('int', "[1,2,3]", True, ListGenerator, [[1, 2, 3]]),
    ('int', "[1,2,'c']", False, None, None),
    ('int', "['a','b','c']", False, None, None),
    ('int', 'rand(1, 20)', True, RangeGenerator, [1, 20]),
    ('int', 'rand(1,20)', True, RangeGenerator, [1, 20]),
    ('int', '10', True, ConstGenerator, ['int', 10]),
    ('int', 'cat', False, None, None),
])
def test_create_generator(type, value, is_valid, generator_class, generator_args):
    if is_valid:
        generator = generator_class(*generator_args)
        assert create_generator(type, value) == generator
    else:
        with pytest.raises(ValueError):
            create_generator(type, value)


if __name__ == '__main__':
    pytest.main([__file__])
