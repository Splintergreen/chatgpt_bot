import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import Redis, RedisStorage
from dotenv import load_dotenv

from handlers import other_handlers, user_handlers
from utils import setup_logger

load_dotenv()

logger = setup_logger('main')

redis: Redis = Redis(host='localhost')
storage: RedisStorage = RedisStorage(redis=redis)


secret_token = os.getenv('TOKEN')
bot: Bot = Bot(secret_token)

dp: Dispatcher = Dispatcher()
dp.include_router(user_handlers.router)
dp.include_router(other_handlers.router)


if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
    logger.info('Bot starting...')
