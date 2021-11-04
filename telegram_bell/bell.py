import logging
import struct
from pathlib import Path

import asyncclick as click
from rich import print
from rich.prompt import Confirm
from rich.traceback import install
from telethon import TelegramClient

from telegram_bell.config import Config
from telegram_bell.exceptions import BadAPIConfiguration
from telegram_bell.notifier import SubscribedChannel, read_messages_from_channel

CONFIG_FILE_PATH = "../.env"
CHANNELS_FILE_PATH = "../subscribed_channels.json"
SESSION_NAME = "session"

log = logging.getLogger("rich")


def setup_config():
    Config.create(CONFIG_FILE_PATH)
    SubscribedChannel.create_config_file(CHANNELS_FILE_PATH)


@click.group(chain=True)
async def cli():
    pass


@click.command(name="run")
async def run_command():
    if not Path(CONFIG_FILE_PATH).exists():
        setup_config()

    config = Config.from_path(CONFIG_FILE_PATH)
    client = TelegramClient(SESSION_NAME, config.api_id, config.api_hash)

    try:
        async with client:
            subscribed_channels = SubscribedChannel.read_from_json(CHANNELS_FILE_PATH)
            while True:
                for channel in subscribed_channels:
                    await read_messages_from_channel(
                        client, channel, CHANNELS_FILE_PATH
                    )
    except struct.error:
        raise BadAPIConfiguration("Connection error. Please, execute 'tbell config'.")


@click.command(name="config")
async def config_command():
    if Path(CONFIG_FILE_PATH).exists() and not Confirm.ask(
        "Config already exist, do you want to create a new one?"
    ):
        return

    setup_config()


install()
cli.add_command(run_command)
cli.add_command(config_command)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
