import logging
import re

from utils.decorator import logger
from utils.decorator import timeit


log = logging.getLogger("discord")


@timeit
@logger
async def parse_arguments(*args) -> dict:
    """Take arguments and turn them into keyword arguments. Split arguments on the '=' character.

    :param args: The arguments to parse.
    :return: A dictionary with keyword arguments.
    """
    forbidden_characters = '[(){},\'"]'
    kwargs = {}
    args = [re.sub(forbidden_characters, '', arg) for arg in args]
    for arg in args:
        if '=' in arg:
            split_arg = arg.split('=')
            kwargs[split_arg[0]] = split_arg[1]
    return kwargs
