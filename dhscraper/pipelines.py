# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import gspread
import re
from itemadapter import ItemAdapter


class DhscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        pattern = r'dh(\d{4})'
        adapter["year"] = re.search(pattern, adapter["origin"]).group(1)
        return item


class GoogleSheetsPipeline:
    def __init__(self):
        gc = gspread.service_account(filename="./creds.json")
        self.sh = gc.open("DH Projects").sheet1

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.sh.append_row([adapter["year"], adapter["origin"], adapter["abstract"]])
        return item
