import logging
from dataclasses import dataclass, asdict
from json import load, dump
from pathlib import Path
from typing import List

from rich.prompt import Confirm, Prompt
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.patched import Message

from telegram_bell.exceptions import SpecifiedChannelDoesNotExist

logger = logging.getLogger("rich")


@dataclass
class SubscribedChannel:
    name: str
    search_keywords: List[str]
    last_id: int = 0

    def update_last_id(self, new_last_id: int, channels_file_path: str):
        self.last_id = new_last_id

        with open(channels_file_path, "r+") as file:
            channels = load(file)
            changed_channels = []
            for channel in channels:
                if channel["name"] == self.name:
                    channel["last_id"] = self.last_id
                changed_channels.append(channel)
            file.seek(0)
            dump(changed_channels, file)
            file.truncate()

    @staticmethod
    def update_existing_channels(channels_file_path: str | Path):
        with open(channels_file_path, "r+") as file:
            channels = load(file)
            changed_channels = []
            for channel in channels:
                if not Confirm.ask(
                    f"Do you want to remove the channel '{channel['name']}'?",
                    default=False,
                ):
                    if search_keywords := Prompt.ask(
                        f"Do you want to change the search keywords of the channel '{channel['name']}'? \n"
                        f"If so, enter the search keywords that will replace the old ones. If not, just press enter",
                        default=False,
                    ):
                        channel["search_keywords"] = search_keywords.split()
                    changed_channels.append(channel)

            while Confirm.ask("Do you want to add a new channel?", default=False):
                name = Prompt.ask("Enter the name of the Telegram channel")
                search_keywords = Prompt.ask(
                    f"Enter your search keywords for the channel '{name}'"
                ).split()
                changed_channels.append(asdict(SubscribedChannel(name, search_keywords)))

            file.seek(0)
            dump(changed_channels, file)
            file.truncate()

    @classmethod
    def read_from_json(
        cls, channels_file_path: str | Path
    ) -> List["SubscribedChannel"]:
        with open(channels_file_path, "r") as file:
            channels = load(file)
        return [SubscribedChannel(**channel) for channel in channels]

    @classmethod
    def show_from_json(cls, channels_file_path: str | Path) -> str | None:
        try:
            channels = SubscribedChannel.read_from_json(channels_file_path)
            return "\n".join([str(channel) for channel in channels])
        except FileNotFoundError:
            logger.error(f"Config doesn't exist. Execute 'tbell config' first, please")

    @classmethod
    def create_config_file(cls, channels_file_path: str | Path):
        channels = []
        while Confirm.ask("Do you want to add a channel?", default=True):
            name = Prompt.ask("Enter the name of the Telegram channel")
            search_keywords = Prompt.ask(
                f"Enter your search keywords for the channel '{name}'"
            ).split()
            channels.append(SubscribedChannel(name, search_keywords))

        with open(channels_file_path, "w") as channels_file:
            channels = [asdict(channel) for channel in channels]
            dump(channels, channels_file)


def keywords_in_message(keywords: List[str], text: str):
    for keyword in keywords:
        if keyword in text.lower():
            return True


async def read_messages_from_channel(
    client: TelegramClient, channel: SubscribedChannel, channels_file_path: str | Path
):
    reverse = channel.last_id != 0

    try:
        messages = await client.get_messages(
            channel.name, min_id=channel.last_id, reverse=reverse
        )
    except (ValueError, FloodWaitError) as e:
        logger.exception(e)
        raise SpecifiedChannelDoesNotExist(
            "Specified channel doesn't exist. Check your config."
        )
    else:
        await handle_messages(channel, channels_file_path, messages)


def must_handle_this_message(channel: SubscribedChannel, message: Message):
    return not channel.search_keywords or (
        channel.search_keywords
        and message.text
        and keywords_in_message(channel.search_keywords, message.text)
    )


async def handle_messages(
    channel: SubscribedChannel, channels_file_path: str, messages, log: bool = False
):
    for message in messages:
        if must_handle_this_message(channel, message):
            if log:
                logger.info(message.sender_id, ":", message.text)
            await message.forward_to("me")
        channel.update_last_id(message.id, channels_file_path)
