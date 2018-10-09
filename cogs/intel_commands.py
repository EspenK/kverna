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
from utils.dataclass import from_dict
from utils.dataclass import merge_dict
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
from utils.command import parse_arguments
from . import config
from . import session

# TODO: Clean up import once commands are finished


log = logging.getLogger('discord')


class IntelCog:

    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(IntelCog(bot))
