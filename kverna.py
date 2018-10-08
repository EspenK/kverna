import discord
from discord.ext import commands
import configparser
import logging.config
from cogs import intel

config = configparser.ConfigParser()
config.read('config/bot.ini')

secret = configparser.ConfigParser()
secret.read('config/secret.ini')

logging.config.fileConfig('config/log.ini')
log = logging.getLogger('discord')

bot = commands.Bot(command_prefix=config['default']['command_prefix'],
                   description=config['default']['description'])


initial_extensions = ['cogs.owner']


if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except (ModuleNotFoundError, discord.errors.ClientException) as e:
            log.error(f'Failed to load {extension}: {e}')
        else:
            log.info(f'{extension} loaded successfully')


@bot.event
async def on_ready():
    log.info(f'Connected as {bot.user}.')


bot.loop.create_task(intel.listen(bot=bot))
bot.run(secret['tokens']['discord_token'])
