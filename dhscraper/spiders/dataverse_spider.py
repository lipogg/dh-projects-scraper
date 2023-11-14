import scrapy
from dhscraper.items import DhscraperItem
import json
import fitz
import io
import logging
from scrapy.spidermiddlewares.httperror import HttpError
from ..utils import extract_urls


class DataverseSpider(scrapy.Spider):
    """identify the spider"""
    name = "dataverse"
    allowed_domains = ["dataverse.nl"]
    start_urls = [
        "https://dataverse.nl/api/search?q=.pdf&subtree=dh2019&per_page=1000",
                  ]
    custom_settings = {'ROBOTSTXT_OBEY': False,
                       'DOWNLOAD_DELAY': 10
                       }

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        response_dict = json.loads(response.body)
        for item in response_dict["data"]["items"]:
            url = item["url"]
            if url is not None:
                yield scrapy.Request(url, callback=self.parse_abstract, errback=self.errback, meta={"start_url": response.url})
            else:
                logging.debug("No download URL found for item: %s", item)

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract xml files
        """
        item = DhscraperItem()
        item["abstract"] = response.url
        item["origin"] = response.meta["start_url"]
        item["http_status"] = response.status
        filestream = io.BytesIO(response.body)
        pdf = fitz.open(stream=filestream, filetype="pdf")
        # extract well-formed urls
        urls = {elem['uri'] for page in pdf for elem in page.get_links() if 'uri' in elem}
        logging.debug('Attribute matches found: %s', urls)
        item["urls"] = urls
        # catch malformed urls: some urls may not be hyperlinks
        abstract = ''.join(page.get_text() for page in pdf)
        #logging.debug('Abstract text: %s', abstract)
        mf_urls = extract_urls(abstract)
        logging.debug('String matches found: %s', mf_urls)
        item["urls"].update(mf_urls)
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

