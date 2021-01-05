from configclasses import configclass


@configclass
class Config:
    api_id: int
    api_hash: str
    channels_file: str = "subscribed_channels.json"
    session_name: str = "session_name"


config = Config.from_path(".env")
