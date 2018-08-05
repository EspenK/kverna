import logging
import asyncio


log = logging.getLogger("discord")


async def fetch(session, url):
    killmail = await session.post(url)
    await asyncio.sleep(0)
    return await killmail.json()
