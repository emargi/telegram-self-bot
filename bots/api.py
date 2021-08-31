from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
import asyncio

class ApiHandlers:
    def __init__(self: 'ApiHandlers', client: TelegramClient):
        """ApiHandlers class for handling api telegram bot events"""
        self.bot = client
        # self.info = asyncio.run(self.bot.get_me())
    
    async def DeletePrivateMessages(self: 'ApiHandlers', event: Message) -> None:
        """Delete private/pv messages"""
        await event.delete()
