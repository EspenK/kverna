from discord.ext import commands
import configparser
import logging.config


config = configparser.ConfigParser()
config.read("config/bot.ini")

secret = configparser.ConfigParser()
secret.read("config/secret.ini")

logging.config.fileConfig("config/log.ini")
log = logging.getLogger("discord")

bot = commands.Bot(command_prefix=config["default"]["command_prefix"],
                   description=config["default"]["description"])


@bot.event
async def on_ready():
    log.info(f'Connected as {bot.user}.')


bot.run(secret["tokens"]["discord_token"])
