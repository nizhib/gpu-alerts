from typing import List

import telegram
from loguru import logger


class BaseClient:
    def __init__(self, token=None, default_channel=None):
        self.token = token
        self.default_channel = default_channel

    def send(self, message, channel=None):
        raise NotImplementedError


class Messenger:
    def __init__(self, clients: List[BaseClient]):
        self.clients = clients

    def send(self, message, channel=None):
        for client in self.clients:
            client.send(message, channel)


class LoguruClient(BaseClient):
    def send(self, message, channel=None):
        prefix = f"[{channel}] " if channel else ""
        logger.info(f"{prefix}{message}")


class TelegramClient(BaseClient):
    @logger.catch()
    def send(self, message, channel=None):
        if self.token is None:
            raise ValueError(f"token is not defined")
        channel = channel or self.default_channel
        if channel is None:
            raise ValueError(f"channel is not defined")

        message = message.replace(".", "\\.")
        message = message.replace("(", "\\(")
        message = message.replace(")", "\\)")
        message = message.replace("-", "\\-")
        message = message.replace("\\\\", "\\")

        bot = telegram.Bot(token=self.token)
        bot.send_message(
            chat_id=f"@{channel}",
            text=message,
            parse_mode=telegram.ParseMode.MARKDOWN_V2,
        )
