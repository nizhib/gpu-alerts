from dataclasses import dataclass
from typing import List, Dict

from loguru import logger


@dataclass
class Entry:
    url: str
    title: str
    price_eu: float
    price_ru: float
    missing: int = 0

    @property
    def total_ru(self) -> float:
        exchange_rate = self.price_ru / self.price_eu
        return (self.price_eu + max(0.0, self.price_eu - 200) * 0.15) * exchange_rate

    def __str__(self):
        return f"{self.total_ru}\t{self.title}"

    def to_markdown(self):
        return (
            f"[{self.title}]({self.url})\n\n"
            + f"{int(self.price_ru):,} ₽".replace(",", " ")
            + (
                f" (с пошлиной будет {int(self.total_ru):,} ₽)".replace(",", " ")
                if self.price_eu > 200
                else ""
            )
        )


class Memory:
    MAX_MISSING = 3

    def __init__(self):
        self.entries: Dict[str, Entry] = dict()

    def update(self, new_entries: List[dict]):
        new_urls = {entry["url"] for entry in new_entries}

        for old_url in self.entries:
            if old_url not in new_urls:
                self.entries[old_url].missing += 1

        added = []
        for entry in new_entries:
            new_url = entry["url"]
            if new_url not in self.entries:
                self.entries[new_url] = Entry(**entry)
                added.append(self.entries[new_url])
                logger.info(f"ADD\t{str(entry)}")
            else:
                self.entries[new_url].missing = 0

        removed = []
        for url, entry in self.entries.items():
            if entry.missing > self.MAX_MISSING:
                removed.append(entry)
                logger.info(f"DEL\t{str(entry)}")
                del self.entries[url]

        return added, removed
