import json
import aiofiles
from dataclasses import asdict

from utils.dataclass import Config
from utils.dataclass import from_dict
from utils.decorator import logger
from utils.decorator import timeit


CONFIG_FILE = 'config/config.json'


@timeit
@logger
async def load() -> Config:
    async with aiofiles.open(file=CONFIG_FILE, mode='r') as file:
        data = await file.read()
        config = json.loads(data)
        return from_dict(cls=Config, dictionary=config)


@timeit
@logger
async def save(config: Config) -> None:
    async with aiofiles.open(file=CONFIG_FILE, mode='w') as file:
        await file.write(json.dumps(obj=asdict(config), indent=4))
