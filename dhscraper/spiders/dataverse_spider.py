import scrapy
from dhscraper.items import DhscraperItem
import json
import fitz
import io
import logging
from scrapy.spidermiddlewares.httperror import HttpError
from ..utils import extract_urls


class DataverseSpider(scrapy.Spider):
    name = "dataverse"
    allowed_domains = ["dataverse.nl"]
    start_urls = [
        "https://dataverse.nl/api/search?q=.pdf&subtree=dh2019&per_page=1000",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_DELAY": 10}

    def parse(self, response):
        """
        Parses the JSON response from Dataverse API and initiates requests for each file URL.

        This method is called for the response object received for the request made for the URL in the start_urls list.
        It processes the JSON response from the Dataverse API, extracting URLs for individual PDF files.
        It then initiates a Scrapy request for each file URL, calling `parse_abstract` as the callback method and
        `errback` if the request returns an HTTP error code.
        """
        response_dict = json.loads(response.body)
        for item in response_dict["data"]["items"]:
            url = item["url"]
            if url is not None:
                yield scrapy.Request(
                    url,
                    callback=self.parse_abstract,
                    errback=self.errback,
                    meta={"start_url": response.url},
                )
            else:
                logging.debug("No download URL found for item: %s", item)

    def parse_abstract(self, response):
        """
        Extracts data from the response object for each of the requests made in the parse method.

        This method extracts the HTTP status code for the response, the originating URL, the abstract URL, and any URLs
        found within the abstract PDFs. Abstracts are converted to plaintext using PyMuPDF. URLS are extracted both from
        hyperlinks within the PDF's pages and from the PDF's text content, which is extracted using PyMuPDF.
        Potentially empty abstracts are flagged.
        """
        item = DhscraperItem()
        item["abstract"] = response.url
        item["origin"] = response.meta["start_url"]
        item["http_status"] = response.status
        filestream = io.BytesIO(response.body)
        urls = set()
        try:
            pdf = fitz.open(stream=filestream, filetype="pdf")
        except (TypeError, ValueError) as e:
            logging.error(f"Error opening PDF (invalid parameter or file type): {e}")
            item["notes"] = "Error processing PDF: Invalid parameter or file type"
        except (
            RuntimeError
        ) as e:  # This catches FileNotFoundError, EmptyFileError, and FileDataError
            logging.error(f"Error opening PDF (runtime error): {e}")
            item["notes"] = "Error processing PDF: Runtime error"
        else:
            # extract well-formed urls
            wf_urls = {
                elem["uri"]
                for page in pdf
                for elem in page.get_links()
                if "uri" in elem
            }
            logging.debug("Attribute matches found: %s", wf_urls)
            urls.update(wf_urls)
            # catch malformed urls: some urls may not be hyperlinks
            abstract_text = "".join(page.get_text() for page in pdf)
            # logging.debug('Abstract text: %s', abstract)
            if len(abstract_text) >= 100:
                mf_urls = extract_urls(abstract_text)
                logging.debug("String matches found: %s", mf_urls)
                urls.update(mf_urls)
            else:
                item["notes"] = "Abstract missing"
        item["urls"] = urls
        yield item

    def errback(self, failure):
        """
        Handles failed requests detected by the httperror middleware.

        This method is invoked when a request generates an error (e.g., connection issues, HTTP error responses).
        It logs the error and yields an item containing details about the failed request.
        """
        logging.error(f"Failed to download {failure.request.url}: {failure.value}")
        item = DhscraperItem()
        item["origin"] = failure.request.meta["start_url"]
        item["abstract"] = failure.request.url
        item["urls"] = set()
        item["notes"] = str(failure.value)
        if failure.check(HttpError):
            item["http_status"] = failure.value.response.status
            logging.info(
                f"Failed with http status code: %s", failure.value.response.status
            )
        yield item
