from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.functions.account import UpdateProfileRequest
import asyncio
from .vc import VoiceChat
from time import perf_counter
import aiocron
from pytz import timezone
from datetime import datetime

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
                cmdToExecute = "INSERT INTO reqs VALUES (1, 0)"
        
        else:
            await event.edit("TimeInBio setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET timeinbio = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0)"
        
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
                cmdToExecute = "INSERT INTO reqs VALUES (0, 1)"
        
        else:
            await event.edit("first comment setted to off")

            if isSettedTheRow(self.conn, self.cursor):
                cmdToExecute = "UPDATE reqs SET firstcomment = 0 WHERE rowid = 1"
            
            else:
                cmdToExecute = "INSERT INTO reqs VALUES (0, 0)"
        
        self.cursor.execute(cmdToExecute)
        self.conn.commit()
    
    async def CommentToChannelsPost(self: 'CliHandlers', event: Message) -> None:
        if not self.cursor.execute("SELECT * FROM reqs WHERE rowid = 1").fetchone() or not self.cursor.execute("SELECT firstcomment FROM reqs WHERE rowid = 1").fetchone()[0]:
            return
        
        await self.bot.send_message((await event.get_chat()), "First comment ⚡️", comment_to=event.id)
    