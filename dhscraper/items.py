# Item model definitions
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
#from scrapy.item import Item, Field


class DhscraperItem(scrapy.Item):
    # item fields
    urls = scrapy.Field()
    origin = scrapy.Field()
    pass
