from pytgcalls import GroupCallFactory
from os import remove
import ffmpeg
from typing import Union

class VoiceChat:
    def __init__(self: 'VoiceChat', client):
        """
        VoiceChat class for handling telegram groups voice chat
        
        Example:
            >>> import asyncio
            >>> vc = VoiceChat(client)
            >>> asyncio.run(vc.Join("chat id")
        """
        self.gcf = GroupCallFactory(client, GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON)
        self.gc = self.gcf.get_file_group_call()
    
    async def Join(self: 'VoiceChat', ChatId: int) -> bool:
        try:
            await self.gc.start(ChatId)
        except:
            return False
        else:
            return True
    
    async def Leave(self: 'VoiceChat') -> bool:
        try:
            await self.gc.stop()
        except:
            return False
        else:
            return True
    
    async def Rejoin(self: 'VoiceChat') -> bool:
        try:
            await self.gc.reconnect()
        except:
            return False
        else:
            return True
    
    async def Play(self: 'VoiceChat', AudioFilePath: str) -> bool:
        self.gc.input_filename = AudioFilePath
    
    async def ConvertAudio(self: 'VoiceChat', InputAudioFilePath: str, OutputAudioFilePath: str) -> Union[str, bool]:
        try:
            ffmpeg.input(InputAudioFilePath).output(
                OutputAudioFilePath, format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
            )

            remove(InputAudioFilePath)
        except:
            return False
        else:
            return OutputAudioFilePath
    
    async def Stop(self: 'VoiceChat') -> bool:
        try:
            await self.gc.stop_playout()
        except:
            return False
        else:
            return True
    
    async def Replay(self: 'VoiceChat') -> bool:
        try:
            await self.gc.restart_playout()
        except:
            return False
        else:
            return True
    
    async def Pause(self: 'VoiceChat') -> bool:
        try:
            await self.gc.pause_playout()
        except:
            return False
        else:
            return True
    
    async def Resume(self: 'VoiceChat') -> bool:
        try:
            await self.gc.resume_playout()
        except:
            return False
        else:
            return True
