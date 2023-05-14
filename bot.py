import os
import asyncio
import openai
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import Redis, RedisStorage
from dotenv import load_dotenv
from handlers import user_handlers, other_handlers

load_dotenv()


redis: Redis = Redis(host='localhost')
storage: RedisStorage = RedisStorage(redis=redis)

OPENAI_KEY: str = os.getenv('OPENAI_KEY')
openai.api_key: str = OPENAI_KEY


secret_token = os.getenv('TOKEN')
bot: Bot = Bot(secret_token)

dp: Dispatcher = Dispatcher()
dp.include_router(user_handlers.router)
dp.include_router(other_handlers.router)


if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
