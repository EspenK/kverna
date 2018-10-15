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
from utils.command import esi_ids_to_lists
from utils.command import esi_names_to_lists
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
    async def filt_add(self, ctx, name: str, *args):
        """Add or update a filter.

        All values are assigned by writing key=value. To see all possible keys use the filter list command.
        :param name: The name of the filer.
        """
        kwargs = await args_to_kwargs(*args)
        kwargs['name'] = name

        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        filt: Filter = discord.utils.find(lambda f: f.name == kwargs.get('name'), guild.filters)

        valid_lists = [guild.lists.get(kwargs.get(element)) for element in ['what', 'where', 'who', 'who_ignore', 'items'] if kwargs.get(element)]
        if None in valid_lists:
            await ctx.send(f'Failed. Make sure the lists already exists.')
            return

        if filt:
            new_filter_dict = {**asdict(filt), **kwargs}
            new_filter = from_dict(cls=Filter, dictionary=new_filter_dict)
            guild.filters.remove(filt)

        else:
            new_filter = from_dict(cls=Filter, dictionary=kwargs)

        config.guilds.remove(guild)
        guild.filters.append(new_filter)
        config.guilds.append(guild)
        await save(config)
        await ctx.send(f'{new_filter}')

    @filt.command(name='remove', aliases=['delete', 'del', 'r'])
    async def filt_remove(self, ctx, name: str):
        """Remove a filter.

        :param name: The name of the filer.
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

    @_list.command(name='list', aliases=['l', 's', 'show'])
    async def list_list(self, ctx, name: str = None):
        """List all list names, or items in a specific list.

        :param name: Name of the list.
        """
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)

        if not name:
            lists = [key for key in guild.lists.keys()]
            await ctx.send(f'Lists: {lists}')
            return

        if guild.lists.get(name):
            response = await esi_names(guild.lists.get(name))
            ids, names = await esi_names_to_lists(list(response))
            await ctx.send(f'Items in list {name}: {names}')
        else:
            await ctx.send(f'List {name} was not found.')

    @_list.command(name='add', aliases=['edit', 'update', 'u', 'a', 'e'])
    async def list_add(self, ctx, name: str, *args):
        """Add or update a list.

        All items (args) must be separated with spaces. Names with spaces need to be in quotes (").

        :param name: Name of the list.
        :param args: Items to add to the list.
        """
        args = await args_to_list(*args)
        response = await esi_ids(args)
        ids, names = await esi_ids_to_lists(response)
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)

        if guild.lists.get(name):
            new_list = list(set(guild.lists.get(name)).union(ids))
        else:
            new_list = ids

        config.guilds.remove(guild)
        guild.lists[name] = new_list
        config.guilds.append(guild)
        await save(config)

        await ctx.send(f'List {name} added {names}')

    @_list.command(name='remove', aliases=['delete', 'del', 'r'])
    async def list_remove(self, ctx, name: str):
        """Remove a list.

        :param name: Name of the list.
        """
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)
        if guild.lists.get(name):
            config.guilds.remove(guild)
            guild.lists.pop(name)
            config.guilds.append(guild)
            await save(config)

            await ctx.send(f'List {name} removed.')
        else:
            await ctx.send(f'List {name} was not found.')


def setup(bot: commands.Bot):
    bot.add_cog(IntelCog(bot))
