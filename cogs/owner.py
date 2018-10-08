import discord
from discord.ext import commands
import asyncio

from utils.decorator import timeit
from utils.decorator import logger


class OwnerCog:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, extension: str):
        """Load an extension.

        :param extension: The dot-path to the extension file.
        """
        asyncio.create_task(self.cog_handler(ctx=ctx, extension=extension, command='load'))

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, extension: str):
        """Unload an extension.

        :param extension: The dot-path to the extension file.
        """
        asyncio.create_task(self.cog_handler(ctx=ctx, extension=extension, command='unload'))

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, extension: str):
        """Reload an extension.

        :param extension: The dot-path to the extension file.
        """
        asyncio.create_task(self.cog_handler(ctx=ctx, extension=extension, command='reload'))

    @timeit
    @logger
    async def cog_handler(self, ctx, extension: str, command: str):
        """Load/ unload/ reload an extension.

        :param extension: The dot-path to the extension file.
        :param command: The command name used to trigger this.
        """
        try:
            if command == 'load':
                self.bot.load_extension(extension)
            elif command == 'unload':
                self.bot.unload_extension(extension)
            elif command == 'reload':
                self.bot.unload_extension(extension)
                self.bot.load_extension(extension)
        except (ModuleNotFoundError, discord.errors.ClientException) as e:
            await ctx.send(f'Failed to reload {extension}: {e}')
        else:
            await ctx.send(f'{extension} reloaded successfully')


def setup(bot: commands.Bot):
    bot.add_cog(OwnerCog(bot))
