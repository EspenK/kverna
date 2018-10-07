from discord.ext import commands
import logging
import asyncio
import aiohttp
import datetime

from utils.decorator import logger
from utils.decorator import timeit
from utils.fetch import fetch
from utils.dataclass import from_dict
from utils.dataclass import Killmail
from utils.dataclass import Attacker
from utils.dataclass import Victim
from utils.dataclass import Item
from utils.dataclass import Zkb
from utils.dataclass import Config
from utils.dataclass import Guild
from utils.dataclass import Filter
from utils.dataclass import Position
from utils.file import load
from utils.file import save
from . import config


log = logging.getLogger('discord')


async def listen(bot: commands.Bot):
    """Listen for new killmail to be available from the zKillboard redisQ.

    When a new killmail is available, fetch it and process it.

    :param bot: The discord bot.
    :return: None.
    """
    await bot.wait_until_ready()

    url = 'https://redisq.zkillboard.com/listen.php?queueID=kverna'

    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": "kverna"}) as session:
        while True:  # TODO: Check connection status
            log.debug('listening')
            zkb_data = await fetch(session=session, url=url)

            if zkb_data is not None and zkb_data.get('package') is not None:
                zkb = from_dict(cls=Zkb, dictionary=zkb_data.get('package').get('zkb'))

                await asyncio.sleep(0.0001)

                killmail_data = await fetch(session=session, url=zkb.href)

                if killmail_data is not None:
                    killmail = from_dict(cls=Killmail, dictionary=killmail_data)

                    await asyncio.sleep(0.0001)

                    asyncio.create_task(process_killmail(zkb=zkb, killmail=killmail, bot=bot))
            else:
                await asyncio.sleep(2)


@timeit
@logger
async def process_killmail(zkb: Zkb, killmail: Killmail, bot: commands.Bot):
    """Process the kill by processing each filter in each guild and look for any matching attributes.

    :param zkb: The zKillboard data for this killmail.
    :param killmail: The killmail.
    :param bot: The discord bot.
    :return: None
    """
    log.info(f'processing killmail {killmail.killmail_id}')
    for guild in config.guilds:
        if guild.reported_killmail_id.get(killmail.killmail_id) is not None:
            return
        for filt in guild.filters:
            asyncio.create_task(process_filter(zkb=zkb, killmail=killmail, guild=guild, filt=filt, bot=bot))
            await asyncio.sleep(0.0001)


@timeit
@logger
async def process_filter(zkb: Zkb, killmail: Killmail, guild: Guild, filt: Filter, bot: commands.Bot):
    matching = []
    await asyncio.sleep(0.0001)


@timeit
@logger
async def add_reported_killmail_id(killmail: Killmail, guild: Guild):
    """Add reported kills to the guilds reported kills list.

    :param killmail: The killmail.
    :param guild: The guild.
    """
    datetime_format = '%Y-%m-%dT%H:%M:%SZ'
    time = datetime.datetime.utcnow()
    config.guilds.remove(guild)
    guild.reported_killmail_id[killmail.killmail_id] = time.strftime(datetime_format)
    config.guilds.append(guild)
    await save(config)