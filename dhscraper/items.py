# Item model definitions
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# from scrapy.item import Item, Field


class DhscraperItem(scrapy.Item):
    # item fields
    urls = scrapy.Field()
    origin = scrapy.Field()
    abstract = scrapy.Field()
    year = scrapy.Field()
    notes = scrapy.Field()
    http_status = scrapy.Field()
    pass
