from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.messages import ReadHistoryRequest
from telethon.errors import PhoneNumberInvalidError
from telethon.tl.types.auth import SentCodeTypeSms
from telethon.tl.types import User
import asyncio
from time import perf_counter
import aiocron
from pytz import timezone
from datetime import datetime
from .utils import (
    CodeRunner,
    OCR,
    VoiceChat,
    YoutubeDownloader,
    AparatDownloader,
    LanguageDemoObject,
    ImageConvertor,
    LiveStream
)
from sys import version
from os import remove
from re import findall
from random import choice

@aiocron.crontab("*/1 * * * *") # Every 1 minute
async def TimeInName() -> None:
    fetchone = CURSOR.execute("SELECT timeinName FROM reqs WHERE rowid = 1").fetchone()

    if not fetchone or not fetchone[0]:
        return
    
    now = datetime.now(timezone("Asia/Tehran"))
    fonts = ["¹²³⁴⁵⁶⁷⁸⁹", "₁₂₃₄₅₆₇₈₉", "①②③④⑤⑥⑦⑧⑨", "𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", "𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿", "『1』『2』『3』『4』『5』『6』『7』『8』『9』", "[̲̅1][̲̅2][̲̅3][̲̅4][̲̅5][̲̅6][̲̅7][̲̅8][̲̅9]"]

    await CLIENT(
        UpdateProfileRequest(
            last_name=f"{now.hour}:{now.minute}".translate(
                f"{now.hour}:{now.minute}".maketrans(
                    "123456789", choice(fonts)
                )
            )
        )
    )

@aiocron.crontab("12 * * * *") # Every 12 hours
async def SendAdsToGroups() -> None:
    fetchone = CURSOR.execute("SELECT * FROM ads WHERE rowid = 1").fetchone()

    if not fetchone or not fetchone[0]:
        return
    
    async for dialog in CLIENT.iter_dialogs():
        if dialog.is_group:
            await CLIENT.send_message(dialog, fetchone[1])
            await asyncio.sleep(1)

class CliHandlers:
    def __init__(self: 'CliHandlers', client: TelegramClient, info, conn, cursor, log, config):
        """CliHandlers class for handling Client telegram bot events"""
        self.bot = client
        self.info = info
        self.vc = VoiceChat(self.bot)
        self.ls = LiveStream(self.bot)
        self.conn = conn
        self.cursor = cursor
        self.log = log
        self.conf = config
        self.language: LanguageDemoObject = self.conf.language

        global CLIENT
        global CONN
        global CURSOR
        CLIENT = self.bot
        CONN = self.conn
        CURSOR = self.cursor
    
    async def SendPanel(self: 'CliHandlers', event: Message) -> None:
        inline_result = await self.bot.inline_query(self.conf.bot_username, "__panel__")

        await event.delete()

        inline_result.result[0].click((await event.get_chat()))
    
    async def SendPing(self: 'CliHandlers', event: Message) -> None:
        await event.edit("pong :)")

    async def VoiceChatHandler(self: 'CliHandlers', event: Message) -> None:
        command = event.text.split(' ')[1].lower()
        available_commands = ["join", "leave", "rejoin", "play", "stop", "replay", "pause", "resume", "volume"]
        success = False

        if not command in available_commands:
            # await event.edit(f"Invalid command!\nMust be among: {', '.join(available_commands)}")
            return await event.edit(self.language.INVALID_COMMAND)
        
        if command == "join":
            chat = await event.get_chat()
            if await self.vc.Join(chat.id):
                await event.delete()
            
            else:
                await event.edit("There is no voice chat in this group!")
        
        elif command == "leave":
            if await self.vc.Leave():
                await event.delete()
            
            else:
                await event.edit("Can not leave voice chat in this group right now!")
        
        elif command == "rejoin":
            if await self.vc.ReJoin():
                success = True
        
        elif command == "play":
            if not event.is_reply:
                return await event.edit("Please reply to an audio file!")
            
            reply_msg = await event.get_reply_message()

            if not reply_msg.audio:
                return await event.edit("Please reply to an audio file!")
            
            await event.edit("Ok, Downloading...")
            
            audio_path = await self.bot.download_media(reply_msg)

            await event.edit("Processing...")
            
            if self.vc.gc.is_audio_running:
                await event.edit("Added to queue")
                return await self.vc.Play(audio_path)
            
            if await self.vc.Play(audio_path):
                return await event.edit("Playing...")
            
            await event.edit("Something went wrong!")

            return remove(audio_path)
        
        elif command == "ytplay":
            if len(event.text.split(' ')) > 2:
                if self.vc.gc.is_audio_running:
                    await event.edit("Added to queue")
                
                if await self.vc.YTPlay(event.text.split(event.text.split(' ')[2])):
                    success = True
            
            else:
                return await event.edit("Please specify youtube video url")
        
        elif command == "stop":
            if await self.vc.Stop():
                success = True
        
        elif command == "replay":
            if await self.vc.Replay():
                success = True
        
        elif command == "pause":
            if await self.vc.Pause():
                success = True
        
        elif command == "resume":
            if await self.vc.Resume():
                success = True

        else:
            if len(event.text.split(' ')) > 2 and event.text.split(' ')[2].isdigit():
                if await self.vc.Volume(int(event.text.split(' ')[2])):
                    success = True
        
        if success:
            return await event.delete()
        
        await event.edit("Something went wrong!")

    async def SendAllDialogs(self: 'CliHandlers', event: Message) -> None:
        dialog_types = ["pv", "groups"]
        wanted_type = event.text.split(' ')[1]

        if wanted_type(' ')[1] not in dialog_types:
            await event.edit("You must insert dialog type between pv, groups !")
            return
        
        chat = await event.get_chat()

        async with self.bot.conversation(chat) as conv:
            await conv.send_message("Ok, now send message you want to send all dialogs you want!")

            message_to_send_all = await conv.get_response()

            while message_to_send_all.sender_id != self.info.id:
                message_to_send_all = await conv.get_response()
            
            await conv.send_message("Ok, now please send send type (between forward and send)!")

            send_type = await conv.get_response()

            while not (send_type.text.lower() in ("forward", "send")) and (send_type.sender_id != self.info.id):
                send_type = await conv.get_response()
            
            await conv.send_message("Ok, now please wait...")

            async for dialog in self.bot.iter_dialogs():
                if ((dialog.is_user) if wanted_type == "pv" else (dialog.is_group)):
                    await self.bot.send_message(dialog, message_to_send_all) if send_type == "send" else self.bot.forward_messages(dialog, message_to_send_all)
                    
                    await asyncio.sleep(0.3)
    
    async def EvalMessageHandler(self: 'CliHandlers', event: Message) -> None:
        code = event.raw_text.replace("eval ", '').replace("eval\n", '')
        
        status = "𝕮𝖔𝖉𝖊:\n<code>{}</code>\n\n𝕽𝖊𝖘𝖚𝖑𝖙:<code>{}</code>\n\n𝕰𝖗𝖗𝖔𝖗𝖘:<code>{}</code>\n\n𝕿𝖎𝖒𝖊:{} seconds"

        await event.edit(status.format(code, "Running...", '', "Running..."), parse_mode="html")

        try:
            start_time = perf_counter()
            real_code = '\n'.join(["  "+c for c in code.split("\n")])
            runner_code = """async def runner(event):\n"""+real_code
            exec(runner_code, globals())
            asyncio.get_running_loop().create_task(runner(event))
        except Exception as e:
            end_time = perf_counter()
            await event.edit(status.format(code, '', str(e), str(end_time - start_time)), parse_mode="html")
        else:
            end_time = perf_counter()
            await event.edit(status.format(code, "Successfully runned", '', str(end_time - start_time)), parse_mode="html")
    
    async def TimeInNameMessageHandler(self: 'CliHandlers', event: Message) -> None:
        command = event.text.split(' ')[1].lower()

        if command not in ["on", "off"]:
            await event.edit("Invalid command!\nCommand must be between <code>on</code>, <code>off</code>", parse_mode="html")
            return
        
        isSettedTheRow = lambda conn, cursor: self.cursor.execute("SELECT timeinName FROM reqs WHERE rowid = 1").fetchone()

        if command == "on":
            await event.edit("TimeInName setted to on")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET timeinName = 1 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (1, 0, 0, 0, 'typing', 0, 0, 0, 0, 'First comment ⚡️')"
        
        else:
            await event.edit("TimeInName setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET TimeInName = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0, 0, 0, 'typing', 0, 0, 0, 0, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def FirstCommentMessageHandler(self: 'CliHandlers', event: Message) -> None:
        command = event.text.split(' ')[2].lower() # e.g ["first", "comment", "on"]

        if command not in ["on", "off"]:
            await event.edit("Invalid command!\nYou must insert between on and off")
            return
        
        isSettedTheRow = lambda conn, cursor: cursor.execute("SELECT firstcomment FROM reqs WHERE rowid = 1").fetchone()

        if command == "on":
            await event.edit("first comment setted to on")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET firstcomment = 1 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 1, 0, 0, 'typing', 0, 0, 0, 0, 'First comment ⚡️')"
        
        else:
            await event.edit("first comment setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET firstcomment = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0, 0, 0, 'typing', 0, 0, 0, 0, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def FirstCommentTextMessageHandler(self: 'CliHandlers', event: Message) -> None:
        text = event.text.lower().replace("comment text ", '').replace("comment text\n", '')

        isSettedTheRow = lambda cursor: cursor.execute("SELECT comment_text FROM reqs WHERE rowid = 1").fetchone()

        await event.edit(f"First comment text setted to {text}")

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET comment_text = '{text}' WHERE rowid = 1"
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, 'typing', 0, 0, 0, 0, '{text}')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def CommentToChannelsPost(self: 'CliHandlers', event: Message) -> None:
        if not self.cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone() or not self.cursor.execute("SELECT firstcomment FROM reqs WHERE rowid = 1").fetchone()[0]:
            return
        
        comment_text = self.cursor.execute("SELECT comment_text FROM reqs WHERE rowid = 1").fetchone()[0]

        try:
            await self.bot.send_message((await event.get_chat()), comment_text, comment_to=event.id)
        except:
            return
    
    async def CodeRunnerMessageHandler(self: 'CliHandlers', event: Message) -> None:
        code = event.raw_text.replace("python3 ", '').replace("python3\n", '')
        status = "𝐿𝒶𝓃𝑔𝓊𝒶𝑔𝑒:\n<code>{}</code>\n\n𝒞𝑜𝒹𝑒:\n<code>{}</code>\n\n𝒪𝓊𝓉𝓅𝓊𝓉:\n<code>{}</code>\n\n𝐸𝓇𝓇𝑜𝓇𝓈:\n<code>{}</code>\n\n𝒯𝒾𝓂𝑒: {} 𝓈𝑒𝒸𝑜𝓃𝒹𝓈"

        cr = CodeRunner(code)

        start_time = perf_counter()
        result = await cr.Run()
        end_time = perf_counter()

        await event.edit(
            status.format(f"Python{version.split(' ')[0]}", code, result.output, result.error, str(end_time - start_time)),
            parse_mode="html"
        )
    
    # Action
    async def ActionMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.raw_text.split(" ")[1].lower()
        if status in ('on', 'off'):
            query = "SELECT * FROM reqs"
            result = self.cursor.execute(query)
            result = result.fetchone()
            if result:
                if result[3]:
                    if result[2]: # dadash migam shenidam age ye session ro hamzaman do ta ja run koni del mishe
                        if status == "off":
                            await event.edit("Action sending status turned off")
                            query = "UPDATE reqs SET action = ?"
                            parameters = (0,)
                        else:
                            await event.edit("Action sending status already is on")
                    else:
                        if status == "on":
                            await event.edit("Action sending status turned on")
                            query = "UPDATE reqs SET action = ?"
                            parameters = (1,)
                        else:
                            await event.edit("Action sending status already is off")
                    if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
                else:
                    query = "SELECT * FROM chats WHERE chat_id = ?"
                    parameters = (event.chat_id,)
                    result = self.cursor.execute(query, parameters)
                    result = result.fetchone()
                    if result:
                        action_status = result[1]
                        if not action_status:
                            if status == "off":
                                await event.edit("sending actions in this chat already is off")
                            elif status == "on":
                                await event.edit("sending action in this chat turned on")
                                query = "UPDATE chats SET action = 1 WHERE chat_id = ?"
                                parameters = (event.chat_id,)
                        elif action_status:
                            if status == "on":
                                await event.edit("sending actions in this chat already is on")
                            elif status == "off":
                                await event.edit("sending action in this chat turned off")
                                query = "UPDATE chats SET action = 0 WHERE chat_id = ?"
                                parameters = (event.chat_id,)
                        if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
                    else:
                        action_status = "off"
                        if status == "on":
                            await event.edit("sending actions in this chat turned on")
                            query = "INSERT INTO chats VALUES(?, ?, ?)"
                            parameters = (event.chat_id, 1, "typing")
                        elif status == "off":
                            await event.edit("sending actions in this chat already is off")
                        if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
            else:
                action_status = "off"
                action_type   = "none"
                if status == "off":
                    await event.edit("sending actions in this chat already is off")
                elif status == "on":
                    await event.edit("sending actions turned on")
                    query = "INSERT INTO reqs VALUES(0, 0, ?, 1, \"typing\", 0, 0)"
                    parameters = (1,)
                if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()          
        else:
            await event.edit("Status can be only on or off")

    async def ActionTypeMessageHandler(self: 'CliHandlers', event: Message) -> None:
        action_type = event.raw_text.split(" ")[-1]
        
        if action_type in (
            'typing',
            'contact',
            'game',
            'location',
            'sticker',
            'record-audio',
            'record-round',
            'record-video',
            'audio',
            'song',
            'round',
            'video',
            'photo',
            'document'
        ):

            result = self.cursor.execute("SELECT * FROM reqs").fetchone()
            if result:
                if result[3]: # If action_aor == All chat, 1 == True Hale :)
                    if not result[4] == action_type:
                        await event.edit("Action type setted to " + action_type)
                        self.cursor.execute("UPDATE reqs SET action_type = ?", (action_type, ))
                        self.conn.commit()
                    else:
                        await event.edit("Action type already is " + action_type)
                else:
                    result = self.cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (event.chat_id,)).fetchone()
                    if result:
                        if not result[2] == action_type:
                            await event.edit("Action type in this chat setted to " + action_type)
                            self.cursor.execute("UPDATE chats SET action_type = ? WHERE chat_id = ?", (action_type, event.chat_id))
                            self.conn.commit()
                        else:
                            await event.edit("Action type in this chat already is " + action_type)
                    else:
                        await event.edit("Action type in this chat setted to " + action_type)
                        self.cursor.execute("INSERT INTO chats VALUES(?, ?, ?)", (event.chat_id, 0, action_type))
                        self.conn.commit()
            else:
                await event.edit("Action type setted to " + action_type)
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, 1, ?, 0, 1, 0, 0, 'First comment ⚡️')", (action_type, ))
                self.conn.commit()
        else:
            await event.edit("action type should be (typing, contact, game, location, sticker, record-audio, record-round, record-video, audio, song, round, video, photo, document) ")
    
    async def ActionAorMessageHandler(self: 'CliHandlers', event: Message) -> None:
        aor = event.raw_text.split(' ')[-1]
        
        if aor.isdigit() and aor in ('0', '1'):
            result = self.cursor.execute("SELECT * FROM reqs").fetchone()
            if result:
                if str(result[3]) == aor:
                    await event.edit("AOR already is " + aor)
                else:
                    await event.edit("AOR Setted to " + aor)
                    self.cursor.execute("UPDATE reqs SET action_aor = ?", (aor,))
                    self.conn.commit()
            else:
                await event.edit("AOR Setted to " + aor)
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, ?, 'typing', 0, 1, 0, 0, 'First comment ⚡️')", (aor,))
                self.conn.commit()
        else:
            await event.edit("AOR Should be 0 or 1")

    async def SendActionHandler(self: 'CliHandlers', event: Message) -> None:
        result = self.cursor.execute("SELECT * FROM reqs").fetchone()
        if result:
            if result[3]:
                if result[2]:
                    async with self.bot.action((await event.get_chat()), result[4]) as action:
                        await asyncio.sleep(4) # 4 seconds
            else:
                result = self.cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (event.chat_id,)).fetchone()
                if result:
                    if result[1]:
                        async with self.bot.action((await event.get_chat()), result[2]) as action:
                            await asyncio.sleep(4) # 4 seconds
    # Markread
    async def MarkreadMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.raw_text.split(" ")[1].lower()
        if status in ('on', 'off'):
            query = "SELECT * FROM reqs"
            result = self.cursor.execute(query)
            result = result.fetchone()
            if result:
                if result[6]:
                    if result[5]:
                        if status == "off":
                            await event.edit("Markread status turned off")
                            query = "UPDATE reqs SET markread = ?"
                            parameters = (0,)
                        else:
                            await event.edit("Markread status already is on")
                    else:
                        if status == "on":
                            await event.edit("Markread status turned on")
                            query = "UPDATE reqs SET markread = ?"
                            parameters = (1,)
                        else:
                            await event.edit("Markread status already is off")
                    if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
                else:
                    query = "SELECT * FROM chats WHERE chat_id = ?"
                    parameters = (event.chat_id,)
                    result = self.cursor.execute(query, parameters)
                    result = result.fetchone()
                    if result:
                        markread_status = result[3]
                        if not markread_status:
                            if status == "off":
                                await event.edit("Markread in this chat already is off")
                            elif status == "on":
                                await event.edit("Markread in this chat turned on")
                                query = "UPDATE chats SET markread = 1 WHERE chat_id = ?"
                                parameters = (event.chat_id,)
                        elif markread_status:
                            if status == "on":
                                await event.edit("Markread in this chat already is on")
                            elif status == "off":
                                await event.edit("Markread in this chat turned off")
                                query = "UPDATE chats SET markread = 0 WHERE chat_id = ?"
                                parameters = (event.chat_id,)
                        if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
                    else:
                        markread_status = "off"
                        if status == "on":
                            await event.edit("Markread in this chat turned on")
                            query = "INSERT INTO chats VALUES(?, ?, ?, ?)"
                            parameters = (event.chat_id, 0, "typing", 1)
                        elif status == "off":
                            await event.edit("Markread in this chat already is off")
                        if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()
            else:
                markread_status = "off"
                if status == "off":
                    await event.edit("Markread in this chat already is off")
                elif status == "on":
                    await event.edit("Markread turned on")
                    query = "INSERT INTO reqs VALUES(0, 0, 0, 1, 'typing', ?, 1, 0, 0, 'First comment ⚡️')"
                    parameters = (1,)
                if ("query" in globals() or "query" in locals()) and "parameters" in globals() or "parameters" in locals(): self.cursor.execute(query, parameters); self.conn.commit()          
        else:
            await event.edit("Status can be only on or off")

    async def MarkreadAorMessageHandler(self: 'CliHandlers', event: Message) -> None:
        aor = event.raw_text.split(' ')[-1]
        
        if aor.isdigit() and aor in ('0', '1'):
            result = self.cursor.execute("SELECT * FROM reqs").fetchone()
            if result:
                if str(result[6]) == aor:
                    await event.edit("AOR already is " + aor)
                else:
                    await event.edit("AOR Setted to " + aor)
                    self.cursor.execute("UPDATE reqs SET markread_aor = ?", (aor,))
                    self.conn.commit()
            else:
                await event.edit("AOR Setted to " + aor)
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, 1, 'typing', 0, ?, 0, 0, 'First comment ⚡️')", (aor,))
                self.conn.commit()
        else:
            await event.edit("AOR Should be 0 or 1")

    async def SendMarkreadHandler(self: 'CliHandlers', event: Message) -> None:
        result = self.cursor.execute("SELECT * FROM reqs").fetchone()
        if result:
            if result[6]:
                if result[5]:
                    await self.bot(ReadHistoryRequest(peer=(await event.get_chat()), max_id=event.id))
            else:
                result = self.cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (event.chat_id,)).fetchone()
                if result:
                    if result[1]:
                        await self.bot(ReadHistoryRequest(peer=(await event.get_chat()), max_id=event.id))
    
    async def deleteMessageHandler(self: 'CliHandlers', event: Message) -> None:
        number = int(event.text.split()[1]) if len(event.text.split()) > 1 else None

        async for msg in self.bot.iter_messages((await event.get_chat()), number):
            await msg.delete()
    
    # Fun
    async def LOLMessageHandler(self: 'CliHandlers', event: Message) -> None:
        emojies = ['😂', '😁', '😃', '😀', '😆', '😄', '🤣', '😹', '😸', '😅']

        for emoji in emojies:
            await event.edit(emoji)
            await asyncio.sleep(2)
    
    async def LikeMessageHandler(self: 'CliHandlers', event: Message) -> None:
        emojies = ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝']

        for emoji in emojies:
            await event.edit(emoji)
            await asyncio.sleep(2)
    
    async def PokerMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        await event.edit(f"poker setted to {status}")

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET poker = {'1' if status == 'on' else '0'} WHERE rowid = 1"
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, {'1' if status == 'on' else '0'}, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def SendPokerToUser(self: 'CliHandlers', event: Message) -> None:
        fetchone = self.cursor.execute("SELECT poker FROM reqs WHERE rowid = 1").fetchone()
        
        if not fetchone or not fetchone[0]:
            return
        
        else:
            await event.reply('😐')
    
    async def BolderMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        await event.edit("Bolder setted to on")

        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'1' if status == 'on' else '0'} WHERE rowid = 1" # bor = bold or italic
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'}, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def ItalicMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        await event.edit("Italicer setted to on")

        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'2' if status == 'on' else '0'} WHERE rowid = 1" # bor = bold or italic or part
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'}, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def PartMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        await event.edit("Parter setted to on")

        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'3' if status == 'on' else '0'} WHERE rowid = 1" # borop = bold or italic or part
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'}, 'First comment ⚡️')"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def OtherMessageHandler(self: 'CliHandlers', event: Message) -> None:
        borop = self.cursor.execute("SELECT borop FROM reqs WHERE rowid = 1").fetchone()

        if not borop or not borop[0]:
            return
        
        elif borop[0] == 1:
            await event.edit(f"**{event.raw_text}**", parse_mode="markdown")
        
        elif borop[0] == 2:
            await event.edit(f"__{event.raw_text}__", parse_mode="markdown")

        elif borop[0] == 3:
            resultText = ''
            text_part = event.raw_text.split() if len(event.raw_text) > 20 else event.raw_text

            for i in text_part:
                resultText += i if type(text_part) == str else i + ' '

                if i in (' ', '\n', '\t'):
                    continue
                
                else:
                    await event.edit(resultText)

        else:
            return
    
    async def SuperForwardMessageHandler(self: 'CliHandlers', event: Message) -> None:
        reply_message = await event.get_reply_message()
        to_chat = event.text.replace("super forward ", '')
        to_chat = to_chat.replace('@', '') if not to_chat.isdigit() else int(to_chat)
        
        try:
            await self.bot.send_message(to_chat, reply_message)
        except:
            await event.edit("Something went wrong!")
        else:
            await event.edit("Successfully forwarded to specified chat!")
    
    async def AdsMessageHandler(self: 'CliHandlers', event: Message) -> None:
        if len(event.text.split()) < 2 and not event.is_reply:
            await event.edit("You must insert command or reply to ads message!")
            return

        fetchone = self.cursor.execute("SELECT * FROM ads WHERE rowid = 1").fetchone()

        if len(event.text.split()) > 1 and event.text.split()[1] == "off":
            await event.edit("Ads setted to off!")
            if fetchone:
                self.cursor.execute("UPDATE ads SET is_off = 1 WHERE rowid = 1")
                self.conn.commit()
            
            return
        
        if event.is_reply:
            await event.edit("Ads setted to on!")

            reply_message = await event.get_reply_message()

            if fetchone:
                cmdToExecute = f"UPDATE ads SET is_off = 1, ad_text = '{reply_message.text}'"
            
            else:
                cmdToExecute = f"INSERT INTO ads VALUES (1, '{reply_message.text}'"
            
            self.cursor.execute(cmdToExecute)
            self.conn.commit()
    
    async def LeachMessageHandler(self: 'CliHandlers', event: Message) -> None:
        group = event.text.split(' ')[1]

        phone_numbers = []

        await event.edit("Please wait...")
        try:
            with open(f"{group}.txt", 'w') as f:
                async for p in self.bot.iter_participants(group, aggressive=True):
                    if p.phone and (p.phone.startswith('+98') or p.phone.startswith('98')):
                        phone_numbers.append(p.phone)
            
                f.write('\n'.join(phone_numbers))
        except Exception as e:
            f.close()
            await event.edit(f"Something went wrong!\n{e}")
        else:
            if len(phone_numbers) > 1:
                await event.respond(file=f"{group}.txt")
                await event.delete()
            
            else:
                await event.edit("Sorry, unable to generate phone number!")
        finally:
            remove(f"{group}.txt")
    
    async def YoutubeDownloaderHandler(self: 'CliHandlers', event: Message) -> None:
        url = event.text.split()[1]
        try:
            ytdl = YoutubeDownloader(url)
        except AttributeError:
            return await event.edit("Invalid youtube link!")
        else:
            await event.edit("Downloading...")
            downloaded_file_path = await ytdl.download()
            await event.delete()
            await event.respond(file=downloaded_file_path)
            remove(downloaded_file_path)
    
    async def TagAllMessageHandler(self: 'CliHandlers', event: Message) -> None:
        mention_message = ' '.join(event.text.split(' ')[1:]) if len(event.text.split()) > 1 else "I tagged you :)"
        mention_list = [[], [], [], [], []] # 2098 * 5
        number = 1
        mention = lambda user: f"<a href=\"tg://user?id={user.id}\">{number}</a>"

        chat = await event.get_chat()

        await event.edit("Please wait...")
        
        async for p in self.bot.iter_participants(chat):
            if p.bot:
                continue
            
            for i in range(5): # the maximum server-side limitation of getting participants methods is 10000
                if number < (i + 1) * 2048: # the maximum length of a message must be 4098 and here we are mentioning (1,2,3,4, e.g) so '1,' * 2048 is 4098
                    mention_list[i].append(mention(p))
                    number += 1
                    break
        
        await event.edit(mention_message)

        for i in mention_list:
            if len(i) > 1:
                message = ','.join(i)
                await event.reply(message, parse_mode="html")

            else:
                break
    
    async def OcrMessageHandler(self: 'CliHandlers', event: Message) -> None:
        reply_message = await event.get_reply_message()
        
        if reply_message.photo:
            await event.edit("Downloading...")

            image_path = await self.bot.download_media(reply_message)
            
            await event.edit("Please wait...")
            
            text = OCR(image_path)

            if text:
                await event.edit(f"Result:\n<code>{text}</code>", parse_mode="html")
            
            else:
                await event.edit("Sorry unable to extract text from image!")

            remove(image_path)
        
        else:
            await event.edit("You must reply to a photo!")
    
    async def CheckPhonesMessageHandler(self: 'CliHandlers', event: Message) -> None:
        phones = findall(r"([\+]*[[0-9][0-9 \-\(\)]{5,})", event.raw_text)
        
        if not phones:
            await event.edit("No phone numbers found in your text!")
            return
        
        status = {} # {"phone": "status"}
        text_to_edit = lambda status: "Result:\n" + '\n'.join([f"{key}: {value}" for key, value in status.items()])
        
        await event.edit(f"{len(phones)} phone number{'s' if len(phones) > 1 else ''} found!\nProcessing... (please wait)")

        for phone in phones:
            status.update({phone: "..."})

            c = TelegramClient("test1", self.conf.api_id, self.conf.api_hash)
            await c.connect()
            
            try:
                sent_code = await c.send_code_request(phone)
            except PhoneNumberInvalidError:
                status.update({phone: "Invalid"})
            else:
                if isinstance(sent_code.type, SentCodeTypeSms):
                    status.update({phone: "Not in telegram!"})
                
                else:
                    status.update({phone: "Active in telegram!"})
            
            await c.disconnect()
            c.session.delete()

            await event.edit(text_to_edit(status))
    
    async def AparatMessageHandler(self: 'CliHandlers', event: Message) -> None:
        aparat_url = event.text.split()[1]
        try:
            aparat_dl = AparatDownloader(aparat_url)
        except AttributeError:
            return await event.edit("Invalid aparat link!")
        else:
            await event.edit("Please wait...")

            info = await aparat_dl.download()
            await event.delete()
            await event.respond(
                f"Title: {info['title']}\nDescription: {info['description']}",
                file=info["downloaded_file_path"]
            )
            remove(info["downloaded_file_path"])

    async def ReverseStickerMessageHandler(self: 'CliHandlers', event: Message) -> None:
        reply_msg = await event.get_reply_message()

        if reply_msg.sticker or reply_msg.photo and not reply_msg.gif:
            await event.edit("Downloading...")
            image_file_path = await self.bot.download_media(reply_msg)

            await event.edit("Converting...")
            converted_file_path = ImageConvertor(image_file_path, f"{'webp' if reply_msg.photo else 'png'}")

            await event.delete()
            await event.respond(file=converted_file_path)

            return remove(converted_file_path)

        await event.edit("Please reply to a photo or sticker file!")

    async def InfoMessageHandler(self: 'CliHandlers', event: Message) -> None:
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            utei: User = await reply_msg.get_sender()
        
        else:
            utei: User = await self.bot.get_me()
    
        profile_photos = await self.bot.get_profile_photos(utei, limit=4)

        await event.respond(
            f"𝓘𝓓: `{utei.id}`\n"
            f"𝓾𝓼𝓮𝓻𝓷𝓪𝓶𝓮: {utei.username if utei.username else ''}\n"
            f"𝓯𝓲𝓻𝓼𝓽 𝓷𝓪𝓶𝓮: `{utei.first_name}`\n"
            f"𝓵𝓪𝓼𝓽 𝓷𝓪𝓶𝓮: {utei.last_name if utei.last_name else ''}\n"
            f"𝓲𝓼 𝓯𝓪𝓴𝓮: {'𝔂𝓮𝓼' if utei.fake else '𝓷𝓸'}\n"
            f"𝓲𝓼 𝓼𝓬𝓪𝓶: {'𝔂𝓮𝓼' if utei.scam else '𝓷𝓸'}\n"
            f"𝓯𝓻𝓸𝓶 𝓼𝓾𝓹𝓹𝓸𝓻𝓽 𝓽𝓮𝓪𝓶: {'𝔂𝓮𝓼' if utei.support else '𝓷𝓸'}\n"
            f"𝓲𝓼 𝓬𝓸𝓷𝓽𝓪𝓬𝓽: {'𝔂𝓮𝓼' if utei.contact else '𝓷𝓸'}\n"
            f"𝓲𝓼 𝓶𝓾𝓽𝓾𝓪𝓵 𝓬𝓸𝓷𝓽𝓪𝓬𝓽: {'𝔂𝓮𝓼' if utei.mutual_contact else '𝓷𝓸'}\n"
            f"𝓭𝓮𝓵𝓮𝓽𝓮𝓭: {'𝔂𝓮𝓼' if utei.deleted else '𝓷𝓸'}\n"
            f"𝓲𝓼 𝓫𝓸𝓽: {'𝔂𝓮𝓼' if utei.bot else '𝓷𝓸'}\n"
            f"𝓱𝓪𝓼 𝓹𝓻𝓸𝓯𝓲𝓵𝓮 𝓹𝓱𝓸𝓽𝓸: {'𝔂𝓮𝓼' if utei.photo else '𝓷𝓸'}\n"
            f"𝓹𝓱𝓸𝓷𝓮 𝓷𝓾𝓶𝓫𝓮𝓻: {utei.phone if utei.phone else '𝓱𝓲𝓭𝓭𝓮𝓷'}",
            file=profile_photos if profile_photos.total else None
        )

        await event.delete()
    
    async def LiveStreamMessageHandler(self: 'CliHandlers', event: Message) -> None:
        command = event.text.split(' ')[1].lower()
        available_commands = ["join", "leave", "rejoin", "play", "stop", "replay", "pause", "resume", "volume"]
        success = False

        if not command in available_commands:
            # await event.edit(f"Invalid command!\nMust be among: {', '.join(available_commands)}")
            return await event.edit(self.language.INVALID_COMMAND)
        
        if command == "join":
            if not len(event.text.split(' ')) > 2:
                return await event.edit("Please specify the channel you want to join")

            chat = event.text.split(' ')[2]
            chat = chat if not chat.isdigit() else int(chat)
            if await self.ls.Join(chat):
                success = True
        
        elif command == "leave":
            if await self.ls.Leave():
                success = True
        
        elif command == "rejoin":
            if await self.ls.ReJoin():
                success = True
        
        elif command == "play":
            if not event.is_reply:
                return await event.edit("Please reply to a video file!")
            
            reply_msg = await event.get_reply_message()

            if not reply_msg.video:
                return await event.edit("Please reply to a video file!")
            
            await event.edit("Ok, Downloading...")
            
            video_path = await self.bot.download_media(reply_msg)

            await event.edit("Processing...")

            if self.ls.gc.is_video_running:
                await event.edit("Added to queue")
                return await self.ls.Play(video_path)
            
            if await self.ls.Play(video_path):
                return await event.edit("Playing...")
            
            await event.edit("Something went wrong!")

            return remove(video_path)
        
        elif command == "ytplay":
            if len(event.text.split(' ')) > 2:
                if await self.ls.gc.is_video_running:
                    await event.edit("Added to queue")
                
                if await self.ls.YTPlay(event.text.split(event.text.split(' ')[2])):
                    success = True
            
            else:
                return await event.edit("Please specify youtube video url")
        
        elif command == "stop":
            if await self.ls.Stop():
                success = True
        
        elif command == "replay":
            if await self.ls.Replay():
                success = True
        
        elif command == "pause":
            if await self.ls.Pause():
                success = True
        
        elif command == "resume":
            if await self.ls.Resume():
                success = True

        else:
            if len(event.text.split(' ')) > 2 and event.text.split(' ')[2].isdigit():
                if await self.ls.Volume(int(event.text.split(' ')[2])):
                    success = True
        
        if success:
            return await event.delete()
        
        await event.edit("Something went wrong!")
