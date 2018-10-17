import discord
from discord.ext import commands
import logging
from dataclasses import asdict
from utils.fetch import (esi_ids, esi_names, esi_search, esi_regions, esi_constellations)
from utils.dataclass import (from_dict, Guild, Filter)
from utils.file import save
from utils.command import (args_to_kwargs, args_to_list, esi_ids_to_lists, esi_names_to_lists)
from . import config


log = logging.getLogger('discord')


class IntelCog:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def on_guild_join(self, guild: discord.Guild):
        if not discord.utils.find(lambda g: g.id == guild.id, config.guilds):
            kwargs = {'id': guild.id,
                      'lists': {},
                      'filters': []}
            new_guild: Guild = from_dict(cls=Guild, dictionary=kwargs)
            config.guilds.append(new_guild)
            await save(config)
            log.info(f'Joined new guild {guild.name}.')
        else:
            log.info(f'Rejoined guild {guild.name}.')

    @commands.command(name='setchannel', aliases=['set_channel', 'sc'])
    async def set_channel(self, ctx, channel: discord.TextChannel = None):
        """Set a channel that the bot will report kills to.

        If no channel is provided, use the channel that the command was used in.

        :param channel: The discord server to use.
        """
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)

        if channel:
            new_channel = channel.id
            new_channel_name = channel.name
            log.debug(f'Guild {guild.id} sets channel {channel.name}, {channel.id}')
        else:
            new_channel = ctx.channel.id
            new_channel_name = ctx.channel.name
            log.debug(f'Guild {guild.id} sets channel {ctx.channel.name}, {ctx.channel.id}')

        config.guilds.remove(guild)
        guild.channel = new_channel
        config.guilds.append(guild)
        await save(config)
        await ctx.send(f'{new_channel_name} set as channel.')

    @commands.command(name='setstaging', aliases=['set_staging'])
    async def set_staging(self, ctx, system: str):
        guild: Guild = discord.utils.find(lambda g: g.id == ctx.guild.id, config.guilds)

        system_response = await esi_search(categories='solar_system', search=system)
        if system_response is None:
            await ctx.send(f'No result found, please be more specific.')
        elif len(system_response) > 1:
            await ctx.send(f'More than one result found, please be more specific.')
        else:
            config.guilds.remove(guild)
            guild.staging = system_response[0]
            config.guilds.append(guild)
            await save(config)
            await ctx.send(f'{system} set as staging.')

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
            if len(str(names)) > 1800:
                await ctx.send(f'List is too big to be sent as one message. Please make several lists instead.')
            else:
                names_str = str(names).replace('\'', '"').replace(',', '')
                await ctx.send(f'Items in list {name}: {names_str}')
        else:
            await ctx.send(f'List {name} was not found.')

    async def region_to_systems(self, args) -> tuple:
        """Takes arguments from a "!list add region" command and returns ids and names of all systems in the regions.

        :param args: Regions to get the systems from.
        :return: A tuple with list of ids and list of names for all systems in the regions.
        """
        args.pop(0)
        systems = []
        for region in args:
            search_response = await esi_search(categories='region', search=region)
            region_response = await esi_regions(search_response[0])
            for constellation in region_response.get('constellations'):
                constellation_response = await esi_constellations(constellation)
                systems += constellation_response.get('systems')

        response = await esi_names(systems)
        ids, names = await esi_names_to_lists(list(response))

        return ids, names

    @_list.command(name='add', aliases=['edit', 'update', 'u', 'a', 'e'])
    async def list_add(self, ctx, name: str, *args):
        """Add or update a list.

        All items (args) must be separated with spaces. Names with spaces need to be in quotes (").

        :param name: Name of the list.
        :param args: Items to add to the list.
        """
        args = await args_to_list(*args)

        if args[0] in ['region', 'regions']:
            ids, names = await self.region_to_systems(args)
        else:
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

        if len(str(names)) > 1800:
            await ctx.send(f'List is too big to be sent as one message. Please make several lists instead.')
        else:
            names_str = str(names).replace('\'', '"').replace(',', '')
            await ctx.send(f'List {name} added {names_str}')

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
