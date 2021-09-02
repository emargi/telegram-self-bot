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
cursor.execute("CREATE TABLE IF NOT EXISTS reqs (timeinbio INTEGER, firstcomment INTEGER, action INTEGER, action_aor INTEGER, action_type TEXT, markread INTEGER, markread_aor INTEGER)") # Setted integer to get/set it as 0 and 1
cursor.execute("CREATE TABLE IF NOT EXISTS chats (chat_id TEXT, action INTEGER, action_type TEXT, markread INTEGER)")
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
    
    bot.add_event_handler(
        handlers.FirstCommentMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^first comment [a-zA-Z]+$")
    )

    # Action handlers
    bot.add_event_handler(
        handlers.ActionMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^action [a-zA-Z]+$")
    )

    bot.add_event_handler(
        handlers.ActionTypeMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^action type [a-zA-Z]+$")
    )

    bot.add_event_handler(
        handlers.ActionAorMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^action aor [a-zA-Z0-9]+$")
    )

    bot.add_event_handler(
       handlers.SendActionHandler,
       events.NewMessage(incoming=True) # (supergroups) or (groups)
    )

    # Markread handlers
    bot.add_event_handler(
        handlers.MarkreadMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^markread [a-zA-Z]+$")
    )

    bot.add_event_handler(
        handlers.MarkreadAorMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^markread aor [a-zA-Z0-9]+$")
    )

    bot.add_event_handler(
        handlers.SendMarkreadHandler,
        events.NewMessage(incoming=True)
    )

    bot.add_event_handler(
        handlers.CommentToChannelsPost,
        events.NewMessage(func=lambda event: event.is_channel and not event.is_group) # Supergroups are channel types too, so if is_group is False and is_channel is True, chat should be a channel type
    )
    
    bot.add_event_handler(
        handlers.CodeRunnerMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"\Apython3[\n ].+")
    )
    
    bot.add_event_handler(
        handlers.LOLMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^lol$")
    )

    bot.add_event_handler(
        handlers.LikeMessageHandler,
        events.NewMessage(outgoing=True, pattern=r"^like$")
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
