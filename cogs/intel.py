from discord.ext import commands
import logging
import asyncio
import aiohttp
import datetime
import itertools

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

    while True:  # TODO: Check connection status
        log.debug('listening')
        zkb_data = await fetch(url=url)

        if type(zkb_data) is dict and zkb_data is not None and zkb_data.get('package') is not None:
            zkb = from_dict(cls=Zkb, dictionary=zkb_data.get('package').get('zkb'))

            await asyncio.sleep(0.0001)

            killmail_data = await fetch(url=zkb.href)

            if type(killmail_data) is dict and killmail_data is not None:
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
            if filt.enabled:
                asyncio.create_task(process_filter(zkb=zkb, killmail=killmail, guild=guild, filt=filt, bot=bot))
                await asyncio.sleep(0.0001)


@timeit
@logger
async def process_filter(zkb: Zkb, killmail: Killmail, guild: Guild, filt: Filter, bot: commands.Bot):
    if killmail.killmail_id in guild.reported_killmail_id:
        return

    coros = []
    await asyncio.sleep(0.0001)

    if filt.where:
        coros.append(is_where(killmail=killmail, guild=guild, filt=filt))

    if filt.isk_value:
        coros.append(is_expensive(zkb=zkb, filt=filt))

    if filt.range:
        coros.append(is_in_range(killmail=killmail, guild=guild, filt=filt))

    if filt.items:
        coros.append(has_items(killmail=killmail, guild=guild, filt=filt))

    if filt.action == 'use':
        if filt.what:
            coros.append(is_what_attacker(killmail=killmail, guild=guild, filt=filt))

        if filt.who:
            coros.append(is_who_attacker(killmail=killmail, guild=guild, filt=filt))

    elif filt.action == 'kill':
        if filt.what:
            coros.append(is_what_victim(killmail=killmail, guild=guild, filt=filt))

        if filt.who:
            coros.append(is_who_victim(killmail=killmail, guild=guild, filt=filt))

    else:
        log.error(f'{guild.id} {filt.name} missing action')

    matching = await asyncio.gather(*coros)

    # TODO: Update the message with embeds and more info
    if False not in matching:
        if killmail.killmail_id not in guild.reported_killmail_id:
            await add_reported_killmail_id(killmail=killmail, guild=guild)
            channel = bot.get_channel(guild.channel)
            if filt.ping:
                await channel.send(
                    f'@here '
                    f'https://zkillboard.com/kill/{killmail.killmail_id} '
                    f'matched {filt.name}')
            else:
                await channel.send(
                    f'https://zkillboard.com/kill/{killmail.killmail_id}/ '
                    f'matched {filt.name}')


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
    staging_system = await fetch(url=f'https://esi.evetech.net/latest/universe/systems/{guild.staging.get("id")}/',
                                 params=params)
    kill_system = await fetch(url=f'https://esi.evetech.net/latest/universe/systems/{killmail.solar_system_id}/',
                              params=params)
    staging_position = from_dict(cls=Position, dictionary=staging_system.get('position'))
    kill_position = from_dict(cls=Position, dictionary=kill_system.get('position'))
    distance = staging_position.distance_in_light_years(kill_position)
    return distance <= filt.range


@timeit
@logger
async def is_what_victim(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if the victim ship is in the filters 'what' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if the victim ship is in the filters 'what' list.
    """
    return killmail.victim.ship_type_id in guild.lists.get(filt.what)


@timeit
@logger
async def is_what_attacker(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if an attackers ship is in the filters 'what' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if an attackers ship is in the filters 'what' list.
    """
    matching = [attacker.ship_type_id in guild.lists.get(filt.what) for attacker in killmail.attackers]
    return True in matching


@timeit
@logger
async def is_who_victim(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if the victim is in the filters 'who' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if the victim is in the filters 'who' list.
    """
    ids = {killmail.victim.alliance_id,
           killmail.victim.corporation_id,
           killmail.victim.character_id,
           killmail.victim.faction_id}
    return bool(ids.intersection(guild.lists.get(filt.who)))


@timeit
@logger
async def is_who_attacker(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if an attacker is in the filters 'who' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if an attacker is in the filters 'who' list.
    """
    ids = set()
    for attacker in killmail.attackers:
        ids.update([attacker.alliance_id,
                    attacker.corporation_id,
                    attacker.character_id,
                    attacker.faction_id])
    return bool(ids.intersection(guild.lists.get(filt.who)))


@timeit
@logger
async def has_items(killmail: Killmail, guild: Guild, filt: Filter) -> bool:
    """Check if an item is in the filters 'items' list.

    :param killmail: The killmail.
    :param guild: The guild.
    :param filt: The filter.
    :return: True if an item is in the filters 'items' list.
    """
    matching = [item.item_type_id in guild.lists.get(filt.items) for item in killmail.victim.items]
    return True in matching
