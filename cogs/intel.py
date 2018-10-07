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
from . import session


log = logging.getLogger('discord')


async def listen(bot: commands.Bot):
    """Listen for new killmail to be available from the zKillboard redisQ.

    When a new killmail is available, fetch it and process it.

    :param bot: The discord bot.
    :return: None.
    """
    await bot.wait_until_ready()

    url = 'https://redisq.zkillboard.com/listen.php?queueID=kverna'

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
    :return: None.
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


@timeit
@logger
async def is_ping(filt: Filter) -> bool:
    """Check if the kill should be pinged (@here)

    :param filt: The filer.
    :return: True if the kill should be pinged (@here).
    """
    return filt.ping == 1


@timeit
@logger
async def is_expensive(zkb: Zkb, filt: Filter) -> bool:
    """Check if the total value is greater than or equal to the value set in the filter.

    :param zkb: The killmail
    :param filt: The filter
    :return: True if the total value is greater than or equal to the value set in the filter
    """
    return zkb.totalValue >= filt.isk_value


@timeit
@logger
async def is_where(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if the solar system matches with the systems in the list referenced in the filter.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if the solar system matches with the systems in the list referenced in the filter.
    """
    return killmail.solar_system_id in guild.lists.get(filt.where)


@timeit
@logger
async def is_in_range(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if the solar system is in range of the staging system.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if the solar system is in range of the staging system.
    """
    params = {'datasource': 'tranquility', 'language': 'en-us'}
    staging_system = await fetch(session=session,
                                 url=f'https://esi.evetech.net/latest/universe/systems/{guild.staging.get("id")}/',
                                 params=params)
    kill_system = await fetch(session=session,
                              url=f'https://esi.evetech.net/latest/universe/systems/{killmail.solar_system_id}/',
                              params=params)
    staging_position = from_dict(cls=Position, dictionary=staging_system.get('position'))
    kill_position = from_dict(cls=Position, dictionary=kill_system.get('position'))
    distance = staging_position.distance_in_light_years(kill_position)
    return distance >= filt.range


@logger
@timeit
async def is_what_victim(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if the victim ship is in the filters 'what' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if the victim ship is in the filters 'what' list.
    """
    return killmail.victim.ship_type_id in guild.lists.get(filt.what)


@logger
@timeit
async def is_what_attacker(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if an attackers ship is in the filters 'what' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if an attackers ship is in the filters 'what' list.
    """
    matching = [attacker.ship_type_id in guild.lists.get(filt.what) for attacker in killmail.attackers]
    return True in matching
