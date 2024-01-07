import scrapy
from dhscraper.items import DhscraperItem
import logging
from ..utils import extract_urls


class ZenodoTXTSpider(scrapy.Spider):
    name = "zenodo_txt"
    allowed_domains = ["zenodo.org"]
    start_urls = [
        "https://zenodo.org/record/1403230/files/dh2017.txt",
    ]

    def parse(self, response):
        """
        Extracts data from the response object for each URL in the start_urls list.

        This method is called for the response object received for the request made for the URL in the
        start_urls list. It extracts the HTTP status code for the response, the originating URL,
        and any URLs found within the response text. URLs are extracted from plain text.
        """

        logging.info("Parse function called on %s", response.url)
        item = DhscraperItem()
        logging.debug("DhscraperItem created")
        item["origin"] = response.url
        item["abstract"] = "NaN"
        item["http_status"] = response.status
        abstract = response.text
        item["urls"] = extract_urls(abstract)
        logging.info("Item ready to be yielded")
        yield item
