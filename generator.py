import json
import logging
import random
import re
import time
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


class SchemaGenerator(Generator):

    def __init__(self, schema: dict[str, str]) -> None:
        logging.debug('attempting to parse the schema')
        self.schema = dict()
        for k, v in schema.items():
            type, value = v.split(':')
            self.schema[k] = create_generator(type, value)
        logging.info('schema parsed successfully')

    def get(self) -> dict[str, str | int | float]:
        result = dict()
        for k, v in self.schema.items():
            result[k] = v.get()
        return result


class TimestampGenerator(Generator):

    def __init__(self) -> None:
        pass
    
    def get(self) -> float:
        return time.time()
    

class ConstGenerator(Generator):

    DEFAULT_CONST_STR = ''
    DEFAULT_CONST_INT = None

    def __init__(self, type: str, value=None) -> None:
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
    
    def get(self) -> str | int:
        return self.value


class RangeGenerator(Generator):

    DEFAULT_MIN = 0
    DEFAULT_MAX = 10_000

    def __init__(self, min: int = DEFAULT_MIN, max: int = DEFAULT_MAX) -> None:
        self.min = min
        self.max = max
    
    def get(self) -> int:
        return random.randint(self.min, self.max)


class ListGenerator(Generator):
    
    def __init__(self, values: list[str] | list[int]) -> None:
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
    
    def get(self) -> str | int:
        return random.choice(list(self.values))


class RandomStrGenerator(Generator):
    
    def __init__(self) -> None:
        pass
    
    def get(self) -> str:
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
