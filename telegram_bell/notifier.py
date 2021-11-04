import logging
from dataclasses import dataclass, asdict
from json import load, dump
from typing import List

from rich import print
from rich.prompt import Confirm, Prompt
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from telegram_bell.exceptions import SpecifiedChannelDoesNotExist

log = logging.getLogger("rich")


@dataclass
class SubscribedChannel:
    name: str
    search_keywords: List[str]
    last_id: int = 0

    def update(self, new_last_id: int, channels_file_path: str):
        self.last_id = new_last_id

        with open(channels_file_path, "r+") as file:
            channels = load(file)
            for channel in channels:
                if channel["name"] == self.name:
                    channel["last_id"] = self.last_id
            file.seek(0)
            dump(channels, file)
            file.truncate()

    @classmethod
    def read_from_json(cls, channels_file_path: str) -> List["SubscribedChannel"]:
        with open(channels_file_path, "r") as file:
            channels = load(file)
        return [SubscribedChannel(**channel) for channel in channels]

    @classmethod
    def create_config_file(cls, channels_file_path: str):
        channels = []
        while Confirm.ask("Do you want to add a channel?"):
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
    client: TelegramClient, channel: SubscribedChannel, channels_file_path: str
):
    reverse = channel.last_id != 0

    try:
        messages = await client.get_messages(
            channel.name, min_id=channel.last_id, reverse=reverse
        )
    except (ValueError, FloodWaitError) as e:
        log.exception(e)
        raise SpecifiedChannelDoesNotExist(
            "Specified channel doesn't exist. Check your config."
        )
    else:
        await handle_messages(channel, channels_file_path, messages)


async def handle_messages(channel, channels_file_path, messages):
    for message in messages:
        if channel.search_keywords:
            if message.text and keywords_in_message(
                channel.search_keywords, message.text
            ):
                print(message.sender_id, ":", message.text)
                await message.forward_to("me")
        else:
            print(message.sender_id, ":", message.text)
            await message.forward_to("me")
        channel.update(message.id, channels_file_path)
