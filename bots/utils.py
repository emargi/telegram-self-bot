import asyncio
from pathlib import Path
from sys import executable
import pytesseract
from PIL import Image
from typing import Union
from pytgcalls import GroupCallFactory
from os import remove
from pytube import YouTube
from youtube_dl import YoutubeDL
from .apis import APIs
from re import match, findall
import aiofiles
import aiohttp
from uuid import uuid4
from os.path import basename, dirname

class Std:
    def __init__(self: 'Std', dictionary: dict):
        self.d = dictionary

    @property
    def output(self: 'Std') -> str:
        return self.d.get("stdout", None)
    
    @property
    def error(self: 'Std') -> str:
        return self.d.get("stderr", None)

async def commandline(command: str) -> Std:
    """
    commandline function for executing commands in system commandline asynchronously
    
    Arguments:
        command: a str object to execute in commandline
    
    Returns:
        an instance of Std object
    
    Example:
        >>> import asyncio
        >>> std = asyncio.run(commandline("ls -a"))
        >>> print(std.output)
        'a_file.txt another_file.py'
        >>> print(std.error)
        None
    
    """
    c = await asyncio.create_subprocess_shell(
        command,
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE
    )

    stdout, stderr = await c.communicate()

    return Std(
        {
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }
    )

class CodeRunner:
    def __init__(self: 'CodeRunner', code: str):
        """
        CodeRunner class for running python3 codes
        
        Args:
            code: a str that contains python3 code
        
        Example:
            >>> import asyncio
            >>> cr = CodeRunner("print('t')")
            >>> result = asyncio.run(cr.Run())
            >>> print(f"Output: {result.output}\nErrors: {result.errors}")
            'Output: t
            Errors: '
        """
        self.code = code
        self.RunnerFilePath = f"{self.curdir}/runner.py"

        with open(self.RunnerFilePath, 'w') as f:
            f.write(self.code)
    
    async def Run(self: 'CodeRunner') -> Std:
        s = await commandline(f"{executable} {self.RunnerFilePath}")

        return s
    
    @property
    def curdir(self: 'CodeRunner') -> str:
        return Path(__file__).parent.resolve()

def OCR(image_path: str) -> Union[str, bool]:
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
    except:
        return None
    else:
        return text if text else None

class VoiceChat:
    def __init__(self: 'VoiceChat', client):
        """
        VoiceChat class for handling telegram application's group/channel voice chats

        Example:
            >>> import asyncio
            >>> import telethon
            >>> client = telethon.TelegramClient(...)
            >>> vc = VoiceChat(client)
            >>> asyncio.run(vc.Join("PySrc"))
        """
        self.client = client
        self.gcf = GroupCallFactory(client, GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON)
        self.gc = self.gcf.get_group_call()
        self.current_audio = None
    
    async def Join(self: 'VoiceChat', chatId) -> bool:
        if not self.gc.is_connected:
            await self.gc.join(chatId)
            return True
        
        return False
    
    async def ReJoin(self: 'VoiceChat') -> bool:
        if not self.gc.is_connected:
            try:
                await self.gc.reconnect()
            except:
                return False
            else:
                return True
        
        return False
    
    async def Leave(self: 'VoiceChat') -> bool:
        if self.gc.is_connected:
            await self.gc.leave()
            remove(self.current_audio)
            return True
        
        return False
    
    async def Play(self: 'VoiceChat', audio_file: str) -> bool:
        if self.gc.is_audio_running:
            await self.Stop()
            
            if audio_file != self.current_audio:
                remove(self.current_audio)
            
            await self.gc.start_audio(audio_file)
            self.current_audio = audio_file
            return True
        
        try:
            await self.gc.start_video("bots/downloads/Telegram-Voice-Chat-2.0-featured.jpg", with_audio=False)
            await self.gc.start_audio(audio_file)
        except Exception as e:
            return False
        else:
            self.current_audio = audio_file
            return True

    async def Stop(self: 'VoiceChat') -> bool:
        if self.gc.is_audio_running:
            await self.gc.stop_audio()
            return True
        
        return False
    
    async def RePlay(self: 'VoiceChat') -> bool:
        if not self.gc.is_audio_running and self.current_audio:
            await self.Play(self.current_audio)
            return True
        
        return False
    
    async def Pause(self: 'VoiceChat') -> bool:
        if self.gc.is_audio_running:
            await self.gc.set_audio_pause(True)
            return True
        
        return False
    
    async def Resume(self: 'VoiceChat') -> bool:
        if self.gc.is_audio_running:
            await self.gc.set_audio_pause(False)
            return True
        
        return False

class YoutubeDownloader:
    def __init__(self, url) -> None:
        self.url = url
    
    def download(self):
        self.file_path = YouTube(self.url).streams.first().download()
        return self.file_path

class AparatDownloader:
    def __init__(self: 'AparatDownloader', url: str):
        """
        AparatDownloader class for downloading aparat videos

        Args:
            url (`str`) : Aparat video URL
        
        Return:
            an instance of (`AparatDownloader`) class
        
        Raise:
            (`AttributeError`) on invalid aparat URLs
        """
        self.url = url
        if not match(r"^http[s]*:\/\/[w\.]*aparat\.com\/v\/\S{5,}", self.url):
            raise AttributeError("Invalid aparat url specified: %s" % self.url)
        
        self.video_id = findall(r"^http[s]*:\/\/[w\.]*aparat\.com\/v\/(\S{5,})", self.url)[0]
    
    async def download(self: 'AparatDownloader') -> dict:
        resp1 = await APIs.Aparat(self.video_id)
        
        if resp1['Ok']:
            dl_file_path = await AioStreamDownload(
                self.url,
                f"aparat{''.join(str(uuid4())[:5])}.mp4"
            )

            return {
                "title": resp1['title']['title'],
                "description": resp1['description']['description'],
                "downloaded_file_path": dl_file_path
            }

        return {}

async def AioStreamDownload(url: str, file_path: str) -> str:
    """
    AioStreamDownload function for downloading specified url opened contents in to specified file_path

    Arguments:
        url (`str`) : The url that you want to download it contents
        file_path (`str`) : The file path you want to download into it
    
    Return:
        (`str`) : The downloaded file path
    
    Example:
        >>> import asyncio
        >>> downloaded_file_path = asyncio.run(
            AioStreamDownload("https://google.com", "google.html")
        )
        >>> print(downloaded_file_path)
        'google.html'
    """
    # Open file_path file specified asynchronously
    async with aiofiles.open(file_path, 'wb') as f:
        # Write new aiohttp client session to use it to requests
        async with aiohttp.ClientSession() as session:
            # Request asynchronously to url with 'GET' method
            async with session.get(url) as resp:
                # get any chunk receiving from the target server as soon as it received
                async for chunk in resp.content.iter_any():
                    # Write chunk in to the file_path specified
                    await f.write(chunk)
    
    return file_path

class LanguageDemoObject:
    PANEL_MAIN = ...
    INVALID_COMMAND = ...

def ImageConvertor(real_file: str, to_filename: str) -> str:
    img = Image.open(real_file)
    rgb_img = img.convert('RGB')
    # to_file = f"{dirname(real_file)}/{basename(real_file).replace(basename(real_file.split('.')[1]), to_filename)}"
    to_file = real_file.replace(basename(real_file), '.'.join([basename(real_file).split('.')[0], to_filename]))
    rgb_img.save(to_file)
    img.close()

    remove(real_file)
    return to_file
