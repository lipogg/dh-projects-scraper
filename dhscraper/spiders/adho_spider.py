import scrapy
from dhscraper.items import DhscraperItem
import logging
from scrapy.spidermiddlewares.httperror import HttpError
from ..utils import extract_urls


class AdhoSpider(scrapy.Spider):

    name = "adho_website"
    allowed_domains = ["dh2020.adho.org"]
    start_urls = [
        "https://dh2020.adho.org/abstracts/",
    ]

    def parse(self, response):
        """
        Initiates requests for the URLs to abstract pages extracted from the website in the start_urls list.

        This method is called for the response object received for the request made for the URL in the
        start_urls list. It extracts and follows all links to individual abstract pages found on the main page,
        calling `parse_abstract` as the callback method and `errback` if the request returns an HTTP error code.
        """
        yield from response.follow_all(xpath="//*[@id='tablepress-9']/tbody/tr/td/a", callback=self.parse_abstract, errback=self.errback, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        Extracts data from the response object for each of the requests made in the parse method.

        This method extracts the HTTP status code for the response, the originating URL, the abstract URL, and any URLs
        found within the response text. URLs are extracted from plain text. Potentially empty abstracts are flagged.
        """
        item = DhscraperItem()
        item["origin"] = response.meta["start_url"]
        item["abstract"] = response.url
        item["http_status"] = response.status
        abstract = response.xpath("//*[@id='index.xml-body.1_div.1']").get()  # returns None if no elements are found
        if abstract is None:
            item["notes"] = "Abstract missing"
        #logging.debug('Abstract text: %s', abstract)
        item["urls"] = extract_urls(abstract)
        logging.info('Item ready to be yielded')
        yield item

    def errback(self, failure):
        """
        Handles failed requests detected by the httperror middleware.

        This method is invoked when a request generates an error (e.g., connection issues, HTTP error responses).
        It logs the error and yields an item containing details about the failed request.
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

