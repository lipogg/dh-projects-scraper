import scrapy
from dhscraper.items import DhscraperItem
import logging
from ..utils import extract_urls


class AdhoSpider(scrapy.Spider):
    """identify the spider"""
    name = "adho_website"
    allowed_domains = ["dh2020.adho.org"]
    start_urls = [
        "https://dh2020.adho.org/abstracts/",
    ]

    def parse(self, response):
        """
        handles the response downloaded for the request made for the start url
        """
        yield from response.follow_all(xpath="//*[@id='tablepress-9']/tbody/tr/td/a", callback=self.parse_abstract, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract web pages
        """
        item = DhscraperItem()
        item["origin"] = response.meta["start_url"]
        item["abstract"] = response.url
        abstract = response.xpath("//*[@id='index.xml-body.1_div.1']").get()
        item["urls"] = extract_urls(abstract)
        logging.info('Item ready to be yielded')
        yield item


