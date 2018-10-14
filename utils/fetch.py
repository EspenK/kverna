import logging
import aiohttp
from utils.decorator import logger
from utils.decorator import timeit
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
    url = 'https://esi.evetech.net/latest/search/'
    params = dict(esi_params)
    params['categories'] = categories
    params['search'] = search
    response = await fetch(url=url, params=params)
    return response.get(categories)


@timeit
@logger
async def esi_regions(region_id: int) -> dict:
    url = f'https://esi.evetech.net/latest/universe/regions/{region_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_constellations(constellation_id: int) -> dict:
    url = f'https://esi.evetech.net/latest/universe/constellations/{constellation_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_systems(system_id: int) -> dict:
    url = f'https://esi.evetech.net/latest/universe/systems/{system_id}/'
    response = await fetch(url=url, params=esi_params)
    return response


@timeit
@logger
async def esi_types(type_id: int) -> dict:
    url = f'https://esi.evetech.net/latest/universe/systems/{type_id}/'
    response = await fetch(url=url, params=esi_params, method='POST')
    return response


@timeit
@logger
async def esi_ids(names: list) -> dict:
    url = f'https://esi.evetech.net/latest/universe/ids/'
    data = str(names).replace('\'', '"')
    response = await fetch(url=url, params=esi_params, data=data, method='POST')
    return response


@timeit
@logger
async def esi_names(ids: list) -> dict:
    url = f'https://esi.evetech.net/latest/universe/names/'
    data = str(ids).replace('\'', '"')
    response = await fetch(url=url, params=esi_params, data=data, method='POST')
    return response
