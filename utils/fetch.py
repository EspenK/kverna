import logging
import aiohttp
from utils.decorator import logger
from utils.decorator import timeit


log = logging.getLogger("discord")


@timeit
@logger
async def fetch(session: aiohttp.ClientSession, url: str, params: dict = None, method: str = 'GET') -> [dict, str, None]:
    """Make a request with the provided method, url and parameters and return the content

    :param session: The session object.
    :param url: The url to request data from.
    :param params: A dictionary of key value pairs to be sent as parameters.
    :param method: The HTTP method to use for the request.
    :return: The contents of the response.
    """
    async with session.request(method=method, url=url, params=params) as response:
        if response.content_type == 'application/json':
            return await response.json()
        else:
            return await response.text()
