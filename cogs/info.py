import discord
from discord.ext import commands
import configparser

from utils.dataclass import Guild
from . import config

bot_config = configparser.ConfigParser()
bot_config.read('config/bot.ini')


class Info:

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='info')
    async def info(self, ctx):
        """Provide some simple information about the bot."""
        guild: Guild = discord.utils.find(lambda m: m.id == ctx.guild.id, config.guilds)
        embed = discord.Embed(title='kverna',
                              description=bot_config['default']['long_description'],
                              color=discord.Color.blue())
        embed.add_field(name="Server count", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="Kills reported",
                        value=f"{len(guild.reported_killmail_id)} to this server")
        embed.add_field(name="Invite",
                        value=f"{bot_config['default']['invite_link']}")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
