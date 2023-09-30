# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import gspread
import re
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DuplicatesPipeline:
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for url in adapter["urls"]:
            if url in self.urls_seen:
                raise DropItem(f"Duplicate item found: {item!r}")
            else:
                self.urls_seen.add(url)
        return item

class DhscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        pattern = r'dh(\d{4})'
        adapter["year"] = re.search(pattern, adapter["origin"], re.IGNORECASE).group(1)

        return item


class GoogleSheetsPipeline:
    def __init__(self):
        gc = gspread.service_account(filename="./creds.json")
        self.sh = gc.open("DH Projects").sheet1
        self.rows = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for url in adapter["urls"]:
            row = [adapter["year"], adapter["origin"], adapter["abstract"], url]
            self.rows.append(row)
        return item

    def close_spider(self, spider):
        self.sh.append_rows(self.rows)
