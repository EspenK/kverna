from discord.ext import commands
import configparser
import logging.config
import asyncio
from aiohttp import ClientSession
from utils import fetch

config = configparser.ConfigParser()
config.read("config/bot.ini")

secret = configparser.ConfigParser()
secret.read("config/secret.ini")

logging.config.fileConfig("config/log.ini")
log = logging.getLogger("discord")

bot = commands.Bot(command_prefix=config["default"]["command_prefix"],
                   description=config["default"]["description"])


async def listen():
    await bot.wait_until_ready()

    url = "https://redisq.zkillboard.com/listen.php?queueID=kverna"
    async with ClientSession() as session:
        while not bot.is_closed():
            killmail = await fetch.fetch(session, url)
            await asyncio.sleep(0)
            log.info(killmail)


@bot.command(name="ping")
async def _ping(ctx):
    await ctx.send("pong!")


@bot.event
async def on_ready():
    log.info(f'Connected as {bot.user}.')


bot.loop.create_task(listen())
bot.run(secret["tokens"]["discord_token"])
