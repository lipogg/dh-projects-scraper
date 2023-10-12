import scrapy
from dhscraper.items import DhscraperItem
import logging
from ..utils import extract_urls



class ZenodoTXTSpider(scrapy.Spider):
    """identify the spider"""
    name = "zenodo_txt"
    allowed_domains = ["zenodo.org"]
    start_urls = [
        "https://zenodo.org/record/1403230/files/dh2017.txt",
    ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        logging.info('Parse function called on %s', response.url)
        item = DhscraperItem()
        logging.debug('DhscraperItem created')
        item["origin"] = response.url
        item["abstract"] = "NaN"
        abstract = response.text
        item["urls"] = extract_urls(abstract)
        logging.info('Item ready to be yielded')
        yield item





