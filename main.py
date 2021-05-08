#!/use/bin/env python3

import asyncio
import os
from typing import List

from arsenic import get_session, browsers, services
from dotenv import load_dotenv

from extractors import CUExtractor
from memory import Entry, Memory
from messaging import TelegramClient, LoguruClient, Messenger

DELAY = 60.0


async def main():
    load_dotenv()

    service = services.Chromedriver(log_file=os.devnull)
    browser = browsers.Chrome()

    telegram_client = TelegramClient(
        token=os.getenv("TG_TOKEN"), default_channel=os.getenv("TG_CHANNEL")
    )
    loguru_client = LoguruClient()
    messenger = Messenger([loguru_client, telegram_client])

    async with get_session(service, browser) as session:
        extractor = CUExtractor(session)
        memory = Memory()

        while True:
            items = await extractor.extract()
            added: List[Entry] = memory.update(items)[0]
            for entry in added:
                messenger.send(entry.to_markdown())
            await asyncio.sleep(DELAY)


if __name__ == "__main__":
    asyncio.run(main())
