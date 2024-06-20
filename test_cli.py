import cli
import pytest
from unittest.mock import patch


ARG_FILE = ['-f', 'file']
ARG_SCHEMA = ['-s', '{\"age\":\"int:rand(1, 100)\"}']
ARGS = ARG_FILE + ARG_SCHEMA


@pytest.mark.parametrize('args,is_valid', [
    (ARG_FILE + ARG_SCHEMA, True),

    (ARGS + ['-c', '10'], True),
    (ARGS + ['-c', '0'], True),
    (ARGS + ['-c', '-10'], False),

    (ARGS + ['-a', 'count'], True),
    (ARGS + ['-a', 'random'], True),
    (ARGS + ['-a', 'uuid'], True),
    (ARGS + ['-a', 'rand'], False),
    (ARGS + ['-a', 'aaa'], False),

    (ARG_FILE + ['-s', '{\"age\":\"int:rand(1, 100)\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:10\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:aaa\"}'], False),
    (ARG_FILE + ['-s', '{\"age\":\"int:[1,50,100]\"}'], True),
    (ARG_FILE + ['-s', '{\"age\":\"int:[1,???,100]\"}'], False),
    (ARG_FILE + ['-s', '{\"age\":\"str:rand(1, 100)\"}'], False),

    (ARG_FILE + ['-s', '{\"name\":\"str:[\'John\',\'Adam\']\"}'], True),
    (ARG_FILE + ['-s', '{\"name\":\"str:[\"John\",\"Adam\"]\"}'], False),

    (ARGS + ['-l', '1000'], True),
    (ARGS + ['-l', '0'], False),
    (ARGS + ['-l', '-1000'], False),

    (ARGS + ['-p', '-10'], False),
    (ARGS + ['-p', '1'], True),
    (ARGS + ['-p', '999'], True)
])
def test_get_arguments(args, is_valid):
    with patch('sys.argv', [''] + args):
        if is_valid:
            cli.get_arguments()
        else:
            with pytest.raises(SystemExit):
                cli.get_arguments()
