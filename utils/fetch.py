import logging
from utils.decorator import (logger, timeit)
from cogs import session


log = logging.getLogger("discord")

esi_params = {'datasource': 'tranquility', 'language': 'en-us'}


@timeit
@logger
async def fetch(url: str, params: dict = None, data = None, method: str = 'GET') -> [dict, str, None]:
    """Make a request with the provided method, url and parameters and return the content

    :param url: The url to request data from.
    :param params: A dictionary of key value pairs to be sent as parameters.
    :param method: The HTTP method to use for the request.
    :return: The contents of the response.
    """
    async with session.request(method=method, url=url, params=params, data=data) as response:
        if response.content_type == 'application/json':
            return await response.json()
        else:
            return await response.text()


@timeit
@logger
async def esi_search(categories: str, search: str) -> list:
    """Search for entities that match a given sub-string.

    :param categories: Type of entities to search for.
    :param search: The string to search on.
    :return: A list of search results.
    """
    url = 'https://esi.evetech.net/latest/search/'
    params = dict(esi_params)
    params['categories'] = categories
    params['search'] = search
    response = await fetch(url=url, params=params)
    return response.get(categories)


@timeit
@logger
async def esi_regions(region_id: int) -> dict:
    """Get information on a region.

    :param region_id: Region ID.
    :return: Information about a region.
    """
    url = f'https://esi.evetech.net/latest/universe/regions/{region_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_constellations(constellation_id: int) -> dict:
    """Get information on a constellation.

    :param constellation_id: Constellation ID.
    :return: Information about a constellation.
    """
    url = f'https://esi.evetech.net/latest/universe/constellations/{constellation_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_systems(system_id: int) -> dict:
    """Get information on a solar system.

    :param system_id: System ID.
    :return: Information about a solar system.
    """
    url = f'https://esi.evetech.net/latest/universe/systems/{system_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_types(type_id: int) -> dict:
    """Get information on a type.

    :param type_id: Type ID.
    :return: Information about a type.
    """
    url = f'https://esi.evetech.net/latest/universe/systems/{type_id}/'
    response = await fetch(url=url, params=esi_params, method='POST')
    return response


@timeit
@logger
async def esi_ids(names: list) -> dict:
    """Resolve a set of names to IDs.

     Resolve a set of names to IDs in the following categories:
     agents, alliances, characters, constellations, corporations factions,
     inventory_types, regions, stations, and systems.
     Only exact matches will be returned.

    :param names: The names to resolve.
    :return: ID/name associations for a set of names divided by category.
    """
    url = f'https://esi.evetech.net/latest/universe/ids/'
    data = str(names).replace('\'', '"')
    response = await fetch(url=url, params=esi_params, data=data, method='POST')
    return response


@timeit
@logger
async def esi_names(ids: list) -> dict:
    """Resolve a set of IDs to names and categories.

    Supported ID’s for resolving are: Characters, Corporations,
    Alliances, Stations, Solar Systems, Constellations, Regions, Types.

    :param ids: The ids to resolve.
    :return: ID/name associations for a set of ID’s.
    """
    url = f'https://esi.evetech.net/latest/universe/names/'
    data = str(ids).replace('\'', '"')
    response = await fetch(url=url, params=esi_params, data=data, method='POST')
    return response
