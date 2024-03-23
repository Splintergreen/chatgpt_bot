from aiogram import Router
from aiogram.types import Message

router: Router = Router()


@router.message()
async def other_message(message: Message):
    await message.delete()
