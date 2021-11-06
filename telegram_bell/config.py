from __future__ import annotations

from pathlib import Path

from configclasses import configclass
from rich.prompt import Prompt


@configclass
class Config:
    api_id: int
    api_hash: str

    @classmethod
    def create(cls, config_file_path: str | Path) -> Config:
        api_id = Prompt.ask("Enter your Telegram API id")
        api_hash = Prompt.ask("Enter your Telegram API hash")

        config = Config(api_id, api_hash)
        with open(config_file_path, "w") as config_file:
            for field in config.__dataclass_fields__:
                value = getattr(config, field)
                config_file.write(f"{field}={value}")
                config_file.write("\n")

        return config
