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

logger = logging.getLogger("rich")

app_path = Path("~/telegram_bell").expanduser()
app_path.mkdir(exist_ok=True)
config_path = app_path / ".env"
channels_file_path = app_path / "subscribed_channels.json"
telegram_session_path = app_path / "session"


async def setup_telegram_session(config: Config):
    client = TelegramClient(str(telegram_session_path), config.api_id, config.api_hash)

    try:
        async with client:
            subscribed_channels = SubscribedChannel.read_from_json(channels_file_path)
            for channel in subscribed_channels:
                logger.info(f"Updating your subscribed channel '{channel}'")
                await read_messages_from_channel(client, channel, channels_file_path)
    except struct.error:
        raise BadAPIConfiguration("Execute 'tbell config' with another parameters.")


async def setup_config(config_exists: bool):
    if config_exists:
        if Confirm.ask(
            "Telegram API config already exist, do you want to create a new one?",
            default=False,
        ):
            Config.create(config_path)
        if Confirm.ask(
            f"\nYour channels: \n"
            f"{SubscribedChannel.show_from_json(channels_file_path)} \n"
            f"Do you want to modify these channels?",
            default=False,
        ):
            SubscribedChannel.update_existing_channels(channels_file_path)
        if Confirm.ask(
            "Telegram session already exist, do you want to create a new one?",
            default=False,
        ):
            config = Config.from_path(config_path)
            await setup_telegram_session(config)
    else:
        Config.create(config_path)
        SubscribedChannel.create_config_file(channels_file_path)
        config = Config.from_path(config_path)
        await setup_telegram_session(config)


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
    client = TelegramClient(str(telegram_session_path), config.api_id, config.api_hash)

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
    config_exists = Path(config_path).exists()
    if config_exists and not Confirm.ask(
        "Config already exist, do you want to modify?", default=False
    ):
        return

    await setup_config(config_exists)


@click.command(name="show")
async def show_command():
    print("Your channels:")
    channels = SubscribedChannel.show_from_json(channels_file_path)
    print(channels)


install()
cli.add_command(run_command)
cli.add_command(config_command)
cli.add_command(show_command)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
