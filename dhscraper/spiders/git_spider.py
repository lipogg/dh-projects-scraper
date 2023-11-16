import scrapy
from dhscraper.items import DhscraperItem
from lxml import etree, html
import json
import logging
from scrapy.spidermiddlewares.httperror import HttpError
from ..utils import extract_urls


class GitSpider(scrapy.Spider):
    """identify the spider"""
    name = "github"
    allowed_domains = ["api.github.com", "raw.githubusercontent.com"]
    start_urls = ["https://api.github.com/repos/ADHO/dh2016/contents/xml",
                  "https://api.github.com/repos/ADHO/dh2015/contents/xml",
                  "https://api.github.com/repos/elliewix/DHAnalysis/contents/DH2014/abstracts",
                  "https://api.github.com/repos/ADHO/data_dh2013/contents/source/tei",
                  "https://api.github.com/repos/747/tei-to-pdf-dh2022/contents/input/files",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/long-papers",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/panels",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/plenaries",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/posters",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/short-papers",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/workshops",
                  ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        logging.info('Parse function called on %s', response.url)
        response_dict = json.loads(response.body)
        for item in response_dict:
            download_url = item["download_url"]
            if download_url is not None:
                yield scrapy.Request(item["download_url"], callback=self.parse_abstract, errback=self.errback, meta={"start_url": response.url})
            else:
                logging.debug("No download URL found for item: %s", item)

    def parse_abstract(self, response):
        item = DhscraperItem()
        logging.debug('DhscraperItem created')
        item["origin"] = response.meta["start_url"]
        item["abstract"] = response.url
        item["http_status"] = response.status
        xml_string = response.body
        urls = set()

        # Determine root and setup for different cases: 2014 BOA is nested in html
        dh2014_in_url = "DH2014" in response.meta["start_url"]
        root = html.fromstring(xml_string) if dh2014_in_url else etree.fromstring(xml_string)
        namespace = "" if dh2014_in_url else "{http://www.tei-c.org/ns/1.0}"

        # Define the parent and child elements to process: non-2014 BOAs have separate back element for bibliography
        parent_tags = ['article', 'body', 'back']
        child_tags = ['a', 'ref', 'ptr']

        # Process parent child tuples and flag found parent elements to detect empty abstracts
        parent_found = False
        abstract_empty = True
        for parent_tag in parent_tags:
            parent_elem = root.find(f'.//{namespace}{parent_tag}')
            logging.debug('Parent found: %s', parent_elem)

            if parent_elem is not None:
                parent_found = True
                for child_tag in child_tags:
                    # Extract well-formed URLs
                    attr_name = 'href' if child_tag == 'a' else 'target'
                    child_elems = parent_elem.findall(f'.//{namespace}{child_tag}') # root.findall
                    logging.debug('Children found: %s', child_elems)
                    wf_urls = {child.attrib[attr_name] for child in child_elems if attr_name in child.attrib}
                    urls.update(wf_urls)
                    logging.debug(f'Attribute matches found in {child_tag} element: {wf_urls}')

                # Catch malformed URLs
                abstract_text = ''.join(parent_elem.itertext())
                if len(abstract_text) >= 100:
                    abstract_empty = False
                mf_urls = extract_urls(abstract_text)
                urls.update(mf_urls)
                logging.debug(f'String matches found in {parent_tag} element: {mf_urls}')

        if not parent_found or abstract_empty:
            item["notes"] = "Abstract missing"
            logging.error(f'Document potentially empty')

        item["urls"] = urls
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


