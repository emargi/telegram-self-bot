from configparser import ConfigParser
from pathlib import Path

class Config:
    def __init__(self: 'Config'):
        """
        Config class for getting config information for bot script

        Example:
            >>> conf = Config()
            >>> print(conf.api_hash)
            'SOMETHING'
        """
        self.conf = ConfigParser()
        self.conf_dir = Path(__file__).parent.resolve()
        self.conf.read(f"{self.conf_dir}/config.ini")
    
    @property
    def api_id(self: 'Config') -> int:
        return int(self.conf.get("info", "api_id"))
    
    @property
    def api_hash(self: 'Config') -> str:
        return self.conf.get("info", "api_hash")
    
    @property
    def bot_token(self: 'Config') -> str:
        return self.conf.get("info", "bot_token")
    
    @property
    def phone_number(self: 'Config') -> str:
        return self.conf.get("info", "phone_number")

    def set_bot_username(self: 'Config', username: str) -> None:
        self.conf.set("info", "bot_username", username)

    @property
    def bot_username(self: 'Config') -> str:
        return self.conf.get("info", "bot_username")
