import logging
import re

from utils.decorator import (logger, timeit)


log = logging.getLogger("discord")


@timeit
@logger
async def args_to_kwargs(*args) -> dict:
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


@timeit
@logger
async def args_to_list(*args) -> list:
    """Take arguments from a command, remove some special characters, and return as a list.

    :param args: The arguments.
    :return: A list of arguments.
    """
    forbidden_characters = '[(){},\'"]'
    args = [re.sub(forbidden_characters, '', arg) for arg in args]
    return list(args)


@timeit
@logger
async def esi_ids_to_lists(response: dict) -> tuple:
    """Take the esi_ids response and make a ids list and a names list and return them as a tuple.

    :param response: The esi_ids response.
    :return: A tuple with two lists, ids and names.
    """
    categories = ['agents',
                  'alliances',
                  'characters',
                  'constellations',
                  'corporations',
                  'factions',
                  'inventory_types',
                  'regions',
                  'stations',
                  'systems']
    ids = []
    names = []
    for category in categories:
        if response.get(category):
            for element in response.get(category):
                ids.append(element.get('id'))
                names.append(element.get('name'))

    return ids, names


@timeit
@logger
async def esi_names_to_lists(response: list) -> tuple:
    """Take the esi_names response and make a ids list and a names list and return them as a tuple.

    :param response: The esi_names response.
    :return: A tuple with two lists, ids and names.
    """
    categories = ['alliance',
                  'character',
                  'constellation',
                  'corporation',
                  'inventory_type',
                  'region',
                  'solar_system',
                  'station']
    ids = []
    names = []
    for element in response:
        ids.append(element.get('id'))
        names.append(element.get('name'))

    return ids, names
