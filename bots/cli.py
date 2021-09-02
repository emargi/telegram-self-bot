from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.messages import ReadHistoryRequest
import asyncio
from .vc import VoiceChat
from time import perf_counter
import aiocron
from pytz import timezone
from datetime import datetime
from .code_runner import CodeRunner
from sys import version

@aiocron.crontab("*/1 * * * *") # Every 1 minute
async def TimeInBio() -> None:
    fetchone = CURSOR.execute("SELECT timeinbio FROM reqs WHERE rowid = 1").fetchone()

    if not fetchone or not fetchone[0]:
        return
    
    now = datetime.now(timezone("Asia/Tehran"))
    await CLIENT(UpdateProfileRequest(about=f"𝕿𝖎𝖒𝖊: {now.hour}:{now.minute}"))

class CliHandlers:
    def __init__(self: 'CliHandlers', client: TelegramClient, conn, cursor, log):
        """CliHandlers class for handling Client telegram bot events"""
        self.bot = client
        self.info = asyncio.get_running_loop().create_task(self.bot.get_me())
        self.vc = VoiceChat(client)
        self.conn = conn
        self.cursor = cursor
        self.log = log

        global CLIENT
        global CONN
        global CURSOR
        CLIENT = self.bot
        CONN = self.conn
        CURSOR = self.cursor
    
    async def SendPing(self: 'CliHandlers', event: Message) -> None:
        await event.edit("pong :)")

    async def VoiceChatHandler(self: 'CliHandlers', event: Message) -> None:
        command = event.text.split(' ')[1].lower()
        available_commands = ["join", "leave", "rejoin", "play", "stop", "replay", "pause", "resume"]

        if not command in available_commands:
            await event.edit(f"Invalid command!\nMust be among: {', '.join(available_commands)}")
            return
        
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
            if await self.vc.Rejoin():
                await event.delete()
            
            else:
                await event.edit("Something went wrong!")
        
        elif command == "play":
            if not event.is_reply:
                await event.edit("Please reply to a audio message!")
                return
            
            reply_msg = await event.get_reply_message()

            if not reply_msg.audio:
                await event.edit("Please reply to a audio message!")
                return
            
            await event.edit("[-] Downloading...")

            audio_file_path = await reply_msg.download()

            await event.edit("[-] Converting...")

            audio_file_path_to_play = await self.vc.ConvertAudio(audio_file_path, "input.raw")

            if not audio_file_path_to_play:
                await event.edit("Something went wrong!")
                return
            
            await event.delete()

            if not await self.vc.Play(audio_file_path_to_play):
                await event.edit("Something went wrong!")
                return
        
        elif command == "stop":
            if await self.vc.Stop():
                await event.delete()
            
            else:
                await event.edit("Something went wrong!")
        
        elif command == "replay":
            if await self.vc.Replay():
                await event.delete()
            
            else:
                await event.edit("Something went wrong!")
        
        elif command == "pause":
            if await self.vc.Pause():
                await event.delete()
            
            else:
                await event.edit("Something went wrong!")
        
        else:
            if await self.vc.Resume():
                await event.delete()
            
            else:
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
    
    async def TimeInBioMessageHandler(self: 'CliHandlers', event: Message) -> None:
        self.log.debug("In TimeInBioMessageHandler asynchronous function")

        command = event.text.split(' ')[1].lower()

        self.log.debug(command)

        if command not in ["on", "off"]:
            await event.edit("Invalid command!\nCommand must be between <code>on</code>, <code>off</code>", parse_mode="html")
            return
        
        isSettedTheRow = lambda conn, cursor: self.cursor.execute("SELECT timeinbio FROM reqs WHERE rowid = 1").fetchone()

        if command == "on":
            await event.edit("TimeInBio setted to on")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET timeinbio = 1 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (1, 0, 0)"
        
        else:
            await event.edit("TimeInBio setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET timeinbio = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0, 0)"
        
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
                cmdToExecute = "INSERT INTO reqs VALUES (0, 1, 0)"
        
        else:
            await event.edit("first comment setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET firstcomment = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0, 0)"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def CommentToChannelsPost(self: 'CliHandlers', event: Message) -> None:
        if not self.cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone() or not self.cursor.execute("SELECT firstcomment FROM reqs WHERE rowid = 1").fetchone()[0]:
            return
        
        await self.bot.send_message((await event.get_chat()), "First comment ⚡️", comment_to=event.id)
    
    async def CodeRunnerMessageHandler(self: 'CliHandlers', event: Message) -> None:
        code = event.raw_text.replace("python3 ", '').replace("python3\n", '')
        status = "𝐿𝒶𝓃𝑔𝓊𝒶𝑔𝑒:\n<code>{}</code>\n\n𝒞𝑜𝒹𝑒:\n<code>{}</code>\n\n𝒪𝓊𝓉𝓅𝓊𝓉:\n<code>{}</code>\n\n𝐸𝓇𝓇𝑜𝓇𝓈:\n<code>{}</code>\n\n𝒯𝒾𝓂𝑒: {} 𝓈𝑒𝒸𝑜𝓃𝒹𝓈"

        cr = CodeRunner(code)

        start_time = perf_counter()
        result = await cr.Run()
        end_time = perf_counter()

        await event.edit(
            status.format(f"Python{version.split(' ')[0]}", code, result.stdout, result.stderr, str(end_time - start_time)),
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
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, 1, ?, 0, 1, 0, 0)", (action_type, ))
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
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, ?, \"typing\", 0, 1, 0, 0)", (aor,))
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
                    query = "INSERT INTO reqs VALUES(0, 0,  0, 1, \"typing\", ?, 1, 0, 0)"
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
                self.cursor.execute("INSERT INTO reqs VALUES(0, 0, 0, 1, \"typing\", 0, ?, 0, 0)", (aor,))
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

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET poker = {'1' if status == 'on' else '0'} WHERE rowid = 1"
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, {'1' if status == 'on' else '0'})"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def SendPokerToUser(self: 'CliHandlers', event: Message) -> None:
        if not self.cursor.execute("SELECT poker FROM reqs WHERE rowid = 1").fetchone():
            return
        
        else:
            await event.reply('😐')
    
    async def BolderMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'1' if status == 'on' else '0'} WHERE rowid = 1" # bor = bold or italic
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'})"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def ItalicMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'2' if status == 'on' else '0'} WHERE rowid = 1" # bor = bold or italic or part
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'})"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def PartMessageHandler(self: 'CliHandlers', event: Message) -> None:
        status = event.text.split()[1].lower()

        if status not in ("on", "off"):
            await event.edit("Invalid command!\nMust be between on and off")
            return
        
        isSettedTheRow = lambda cursor: cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone()

        if isSettedTheRow(self.cursor):
            cmdToExecute = f"UPDATE reqs SET borop = {'3' if status == 'on' else '0'} WHERE rowid = 1" # borop = bold or italic or part
        
        else:
            cmdToExecute = f"INSERT INTO reqs VALUES (0, 0, 0, 0, '', 0, 0, 0, {'1' if status == 'on' else '0'})"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def OtherMessageHandler(self: 'CliHandlers', event: Message) -> None:
        borop = self.cursor.execute("SELECT borop FROM reqs WHERE rowid = 1").fetchone()

        if not borop:
            return
        
        else:
            if borop == 1:
                await event.edit(f"**{event.raw_text}**", parse_mode="markdown")
            
            elif borop == 2:
                await event.edit(f"__{event.raw_text}__", parse_mode="markdown")

            else:
                resultText = ''
                for i in event.raw_text.split(): # kalame be kaleme
                    resultText += i

                    await event.edit(resultText)
    