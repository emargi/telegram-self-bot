from telethon import TelegramClient, events, Button
from telethon.tl.custom.message import Message
import asyncio

class utils:
    PANELBUTTONS = [
        [
            Button.inline("ping", "panel,ping"),
            Button.inline("voice chat", "panel,vc"),
            ...
        ]
    ]

class ApiHandlers:
    def __init__(self: 'ApiHandlers', client: TelegramClient):
        """ApiHandlers class for handling api telegram bot events"""
        self.bot = client
        self.info = asyncio.get_running_loop().create_task(self.bot.get_me())
    
    async def DeletePrivateMessages(self: 'ApiHandlers', event: Message) -> None:
        """Delete private/pv messages"""
        await event.delete()
    
    async def PanelInlineQueryHandler(self: 'ApiHandlers', event: events.InlineQuery.Event) -> None:
        builder = event.builder

        await event.answer(
            [
                builder.article(
                    "Panel",
                    "click to show panel",
                    text = "سلام مدیر گرامی به پنل مدیریتی خود خوش آمدید :)\nلطفا از دکمه های پایین این پیام استفاده کنید!",
                    buttons=utils.PANELBUTTONS
                )
            ]
        )
    