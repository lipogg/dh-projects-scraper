import scrapy
from dhscraper.items import DhscraperItem
import logging
from scrapy.spidermiddlewares.httperror import HttpError
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
        yield from response.follow_all(xpath="//*[@id='tablepress-9']/tbody/tr/td/a", callback=self.parse_abstract, errback=self.errback, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract web pages
        """
        item = DhscraperItem()
        item["origin"] = response.meta["start_url"]
        item["abstract"] = response.url
        item["http_status"] = response.status
        abstract = response.xpath("//*[@id='index.xml-body.1_div.1']").get()
        #logging.debug('Abstract text: %s', abstract)
        item["urls"] = extract_urls(abstract)
        logging.info('Item ready to be yielded')
        yield item

    def errback(self, failure):
        """
        handles failed requests not handled by the downloader middleware
        """
        logging.error(f'Failed to download {failure.request.url}: {failure.value}')
        item = DhscraperItem()
        item["origin"] = failure.request.meta["start_url"]
        item["abstract"] = failure.request.url
        item["urls"] = set()
        item["notes"] = str(failure.value)
        if failure.check(HttpError):
            item["http_status"] = failure.value.response.status
            logging.info(f'Failed with http status code: %s', failure.value.response.status)
        yield item

