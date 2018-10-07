import asyncio
import aiohttp
from utils.file import load


loop = asyncio.get_event_loop()
config = loop.run_until_complete(load())

headers = {"User-Agent": "kverna"}
session = aiohttp.ClientSession(headers=headers, loop=loop)
