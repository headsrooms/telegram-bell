import logging
import struct
from pathlib import Path

import asyncclick as click
from configclasses.configclasses import dump
from configclasses.exceptions import ConfigFilePathDoesNotExist
from rich.prompt import Confirm
from rich.traceback import install
from telethon import TelegramClient

from telegram_bell.config import Config
from telegram_bell.exceptions import BadAPIConfiguration
from telegram_bell.notifier import SubscribedChannel, read_messages_from_channel

SESSION_NAME = "session"

log = logging.getLogger("rich")

app_path = Path("~/telegram_bell").expanduser()
app_path.mkdir(exist_ok=True)
config_path = app_path / ".env"
channels_file_path = app_path / "subscribed_channels.json"


def setup_config():
    Config.create(config_path)
    SubscribedChannel.create_config_file(channels_file_path)


@click.group(chain=True)
async def cli():
    pass


@click.command(name="run")
async def run_command():
    try:
        config = Config.from_path(config_path)
    except ConfigFilePathDoesNotExist:
        config = Config.create(config_path)
        dump(config, config_path)
    client = TelegramClient(SESSION_NAME, config.api_id, config.api_hash)

    try:
        async with client:
            subscribed_channels = SubscribedChannel.read_from_json(channels_file_path)
            while True:
                for channel in subscribed_channels:
                    await read_messages_from_channel(
                        client, channel, channels_file_path
                    )
    except struct.error:
        raise BadAPIConfiguration("Connection error. Please, execute 'tbell config'.")


@click.command(name="config")
async def config_command():
    if Path(config_path).exists() and not Confirm.ask(
        "Config already exist, do you want to create a new one?"
    ):
        return

    setup_config()


install()
cli.add_command(run_command)
cli.add_command(config_command)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")