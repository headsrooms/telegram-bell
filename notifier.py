from dataclasses import dataclass
from json import load, dump
from typing import List

from telethon import TelegramClient

from config import config

client = TelegramClient(config.session_name, config.api_id, config.api_hash)


@dataclass
class SubscribedChannel:
    name: str
    search_keywords: List[str]
    last_id: int = 0

    def update(self, new_last_id: int, file_name: str):
        self.last_id = new_last_id

        with open(file_name, "r+") as file:
            channels = load(file)
            for channel in channels:
                if channel["name"] == self.name:
                    channel["last_id"] = self.last_id
            file.seek(0)
            dump(channels, file)
            file.truncate()

    @classmethod
    def read_from_json(cls, file) -> List["SubscribedChannel"]:
        with open(file, "r") as file:
            channels = load(file)
        return [SubscribedChannel(**channel) for channel in channels]


subscribed_channels = SubscribedChannel.read_from_json(config.channels_file)


def keywords_in_message(keywords: List[str], text: str):
    for keyword in keywords:
        if keyword in text.lower():
            return True


async def read_messages_from_channel(channel: SubscribedChannel, file_name: str):
    reverse = channel.last_id != 0
    async for message in client.iter_messages(
        channel.name, min_id=channel.last_id, reverse=reverse
    ):
        if channel.search_keywords:
            if message.text and keywords_in_message(
                channel.search_keywords, message.text
            ):
                print(message.sender_id, ":", message.text)
                await message.forward_to("me")
        else:
            print(message.sender_id, ":", message.text)
            await message.forward_to("me")
        channel.update(message.id, file_name)


async def main():
    for channel in subscribed_channels:
        while True:
            await read_messages_from_channel(channel, config.channels_file)


with client:
    client.loop.run_until_complete(main())
