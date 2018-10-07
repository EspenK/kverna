import asyncio
from utils.file import load


loop = asyncio.get_event_loop()
config = loop.run_until_complete(load())
