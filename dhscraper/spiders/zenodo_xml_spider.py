from scrapy.spiders import XMLFeedSpider
from dhscraper.items import DhscraperItem
import logging
from ..utils import extract_urls


class ZenodoXMLSpider(XMLFeedSpider):
    """identify the spider"""
    name = "zenodo_xml"
    allowed_domains = ["zenodo.org"]
    start_urls = [
        "https://zenodo.org/record/8210808/files/DH2023_BookOfAbstracts_v2.xml",
    ]
    namespaces = [('tei', 'http://www.tei-c.org/ns/1.0')]
    iterator = "iternodes"
    itertag = "TEI"

    def parse_node(self, response, node):
        """
        handles the response downloaded for the request made for the start url
        """
        item = DhscraperItem()
        item["origin"] = response.url
        item["abstract"] = node.xpath('@n').get()
        urls = set(node.xpath('.//ref/@target', namespaces=self.namespaces).getall()) #item["urls"] = set(...)
        logging.debug('Attribute matches found: %s', urls)
        item["urls"] = urls
        # catch malformed urls: Several urls are not <ref> element attributes, but plain text in <p> or <bibl> elements
        body_elems = node.xpath('.//p|.//bibl', namespaces=self.namespaces).getall()
        body_text = ''.join(body_elems)
        logging.debug('Body extracted: %s', body_text)
        mf_urls = extract_urls(body_text)
        logging.debug('String matches found: %s', mf_urls)
        item["urls"].update(mf_urls)
        yield item




