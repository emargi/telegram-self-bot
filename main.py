from config import Config
from bots import ApiHandlers, CliHandlers
from telethon import TelegramClient, events
import asyncio
import sqlite3
import logging

# Logging
logger = logging.basicConfig(level=logging.ERROR)

# Config
config = Config()

# Database connection
connect = sqlite3.connect("database.db")
cursor = connect.cursor()

# Database requirements
cursor.execute("CREATE TABLE IF NOT EXISTS reqs (timeinbio INTEGER, firstcomment INTEGER)") # Setted integer to get/set it as 0 and 1
connect.commit()

# Bots handlers
async def CliBot(conf: Config, connect, cursor, logger) -> None:
    bot = await TelegramClient(
        "cli",
        api_id = conf.api_id,
        api_hash = conf.api_hash
    ).start(conf.phone_number)

    handlers = CliHandlers(bot, connect, cursor, logger)

    bot.add_event_handler(
        handlers.SendPing,
        events.NewMessage(outgoing=True, pattern=r"^ping|پینگ$")
    )

    bot.add_event_handler(
        handlers.VoiceChatHandler,
        events.NewMessage(outgoing=True, pattern=r"^vc [a-zA-Z]+$", func=lambda event: event.is_group)
    )
    
    bot.add_event_handler(
        handlers.SendAllDialogs,
        events.NewMessage(outgoing=True, pattern=r"^sendall [a-zA-Z]+$")
    )
    
    bot.add_event_handler(
        handlers.EvalMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"\Aeval[\n ].+")
    )
    
    bot.add_event_handler(
        handlers.TimeInBioMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^timeinbio [a-zA-Z]+$")
    )
    
    await bot.run_until_disconnected()

async def ApiBot(conf: Config) -> None:
    bot = await TelegramClient(
        "api",
        api_id = conf.api_id,
        api_hash = conf.api_hash
    ).start(bot_token=conf.bot_token)

    handlers = ApiHandlers(bot)

    bot.add_event_handler(
        handlers.DeletePrivateMessages,
        events.NewMessage(func=lambda event: event.is_private)
    )

    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            *(CliBot(config, connect, cursor, logger), ApiBot(config))
        )
    )
    loop.run_forever()
    loop.close()
