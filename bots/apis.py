import aiohttp
from json import loads

class APIs:
    """APIs class for accessing some APIs"""
    async def MTProxy() -> list:
        async with aiohttp.ClientSession() as session:
            resp = await session.get("https://api.codebazan.ir/mtproto/json")

            json_resp = loads(
                (await resp.read()).decode()
            )

            makeUrl = lambda server, port, secret: f"https://t.me/proxy?server={server}&port={port}&secret={secret}"


        return [makeUrl(i["server"], i["port"], i["secret"]) for i in json_resp["Result"]]
    
    async def Aparat(video_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.codebazan.ir/aparat/?type=id&id=%s" % video_id
            ) as resp:
                json_resp = loads(
                    (await resp.read()).decode()
                )
        
        return json_resp
    