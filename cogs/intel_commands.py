import discord
from discord.ext import commands
import logging
import asyncio
import aiohttp
import datetime
from dataclasses import asdict
from dataclasses import fields

from utils.decorator import logger
from utils.decorator import timeit
from utils.fetch import fetch
from utils.fetch import esi_ids
from utils.fetch import esi_names
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
from utils.command import args_to_kwargs
from utils.command import args_to_list
from . import config
from . import session

# TODO: Clean up import once commands are finished


log = logging.getLogger('discord')


class IntelCog:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name='filter', aliases=['f'])
    @commands.guild_only()
    async def filt(self, ctx):
        """Command group for all filter commands."""
        pass

    @filt.command(name='list', aliases=['l', 's', 'show'])
    async def filt_list(self, ctx):
        """List all filters for this server."""
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        msg = ''
        for filt in guild.filters:
            msg += '\n' + str(filt)
        await ctx.send(msg)

    @filt.command(name='add', aliases=['edit', 'update', 'u', 'a', 'e'])
    async def filt_add(self, ctx, *args):
        """Add or update a filter.

        A filter needs a name.
        All values are assigned by writing key=value. To see all possible keys use the filter list command.
        """
        kwargs = await args_to_kwargs(*args)
        new_filter = None
        if kwargs.get('name') is None:
            await ctx.send('A filter must have a name.')
            return

        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        filt: Filter = discord.utils.find(lambda f: f.name == kwargs.get('name'), guild.filters)

        if filt is not None:
            new_filter_dict = {**asdict(filt), **kwargs}
            new_filter = from_dict(cls=Filter, dictionary=new_filter_dict)
            guild.filters.remove(filt)

        if new_filter is None:
            new_filter = from_dict(cls=Filter, dictionary=kwargs)

        config.guilds.remove(guild)
        guild.filters.append(new_filter)
        config.guilds.append(guild)
        await save(config)
        await ctx.send(f'{new_filter}')

    @filt.command(name='remove', aliases=['delete', 'del', 'r'])
    async def filt_remove(self, ctx, name):
        """Remove a filter.

        :param name: The name of the filer to remove.
        """
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        filt: Filter = discord.utils.find(lambda f: f.name == name, guild.filters)
        if filt is not None:
            config.guilds.remove(guild)
            guild.filters.remove(filt)
            config.guilds.append(guild)
            await save(config)
            await ctx.send(f'Filter {name} removed.')
            return

        await ctx.send(f'Filter {name} was not found.')

    @commands.group(name='list', aliases=['l'])
    async def _list(self, ctx):
        pass

    @_list.command(name='add', aliases=['edit', 'update', 'u', 'a', 'e'])
    async def list_add(self, ctx, name: str, *args):
        names = await args_to_list(*args)
        response = await esi_ids(names)
        categories = ['agents', 'alliances', 'characters', 'constellations',
                      'corporations', 'factions', 'inventory_types', 'regions',
                      'stations', 'systems']
        ids = []
        response_names = []
        for category in categories:
            if response.get(category):
                for element in response.get(category):
                    ids.append(element.get('id'))
                    response_names.append(element.get('name'))
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        config.guilds.remove(guild)
        guild.lists[name] = ids
        config.guilds.append(guild)

        await ctx.send(f'List {name} added {response_names}')


def setup(bot: commands.Bot):
    bot.add_cog(IntelCog(bot))
