import asyncio
from typing import List, Optional

from arsenic import Session
from arsenic.session import Element

__all__ = ["CUExtractor"]


class BaseItemsExtractor:
    async def extract_items(self, session: Session):
        raise NotImplementedError


class CUItemsExtractor(BaseItemsExtractor):
    DELAY = 60.0
    URL = "https://www.computeruniverse.net/en/c/hardware-components/pci-express-graphics-cards"
    PARAMS = "toggle[deliverydatenow]=true"
    INSTOCK = "In stock and immediately available"

    async def extract_items(self, session: Session):
        await session.get(f"{self.URL}?{self.PARAMS}")
        # noinspection PyTypeChecker
        dy = (await session.get_window_size())["height"]
        y = 0
        for _ in range(5):
            await asyncio.sleep(0.5)
            y += dy
            await session.execute_script(f"window.scrollTo(0, {y})")
        return await session.get_elements("div[class='c-productItem']")


class BaseFieldsExtractor:
    async def extract_fields(self, item: Element) -> dict:
        return {
            "url": await self.extract_url(item),
            "title": await self.extract_title(item),
            "price_eu": await self.extract_eu_price(item),
            "price_ru": await self.extract_ru_price(item),
        }

    async def extract_url(self, item: Element) -> str:
        raise NotImplementedError

    async def extract_title(self, item: Element) -> str:
        raise NotImplementedError

    async def extract_eu_price(self, item: Element) -> float:
        raise NotImplementedError

    async def extract_ru_price(self, item: Element) -> float:
        raise NotImplementedError


class CUFieldsExtractor(BaseFieldsExtractor):
    async def extract_url(self, item: Element) -> str:
        el = await item.get_element("a[class='c-productItem__head__name']")
        return await el.get_attribute("href")

    async def extract_title(self, item: Element) -> str:
        el = await item.get_element("a[class='c-productItem__head__name']")
        return (await el.get_attribute("text")).strip()

    async def extract_eu_price(self, item: Element) -> float:
        el = await item.get_element("div[class='price price--blue-4xl flex']")
        innerHTML = await el.get_attribute("innerHTML")
        return float(
            innerHTML.replace("<span>", "")
            .replace("</span>", "")
            .replace("<sup>", "")
            .replace("</sup>", "")
            .replace("&nbsp;", "")
            .replace(".", "")
            .replace(",", ".")[:-1]
        )

    async def extract_ru_price(self, item: Element) -> float:
        el = await item.get_element("div[class='price price--grey-alt flex']")
        innerHTML = await el.get_attribute("innerHTML")
        return float(
            innerHTML.replace("<span>", "")
            .replace("</span>", "")
            .replace("<sup>", "")
            .replace("</sup>", "")
            .replace("&nbsp;", "")
            .replace(".", "")
            .replace(",", ".")[:-1]
        )


class BaseExtractor:
    TOP_GPUS = ["3070", "3080", "3090", "6700", "6800", "6900"]

    def __init__(self, session: Session):
        self.session = session
        self.items_extractor: Optional[BaseItemsExtractor] = None
        self.fields_extractor: Optional[BaseFieldsExtractor] = None

    async def extract(self) -> Optional[List[dict]]:
        items = await self.items_extractor.extract_items(self.session)
        results = []
        for item in items:
            fields = await self.fields_extractor.extract_fields(item)
            if any([top in fields["title"] for top in self.TOP_GPUS]):
                results.append(fields)
        return results


class CUExtractor(BaseExtractor):
    def __init__(self, session: Session):
        super().__init__(session)
        self.items_extractor = CUItemsExtractor()
        self.fields_extractor = CUFieldsExtractor()
