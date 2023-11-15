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
        item["http_status"] = response.status
        urls = set(node.xpath('.//ref/@target', namespaces=self.namespaces).getall())  # .getall() returns empty list if no elements are matched
        logging.debug('Attribute matches found: %s', urls)
        # catch malformed urls: Several urls are not <ref> element attributes, but plain text in <p> or <bibl> elements
        # statt p und bibl body und back wie bei gitspider
        abstract_elems = node.xpath('.//body//text()|.//back//text()', namespaces=self.namespaces).getall() # returns an emtpy list if no elements are found
        abstract_text = ''.join(abstract_elems)
        # logging.debug('Body extracted: %s', body_text)
        if len(abstract_text) >= 100:
            mf_urls = extract_urls(abstract_text)
            logging.debug('String matches found: %s', mf_urls)
            urls.update(mf_urls)
        else:
            item["notes"] = "Abstract missing"
        item["urls"] = urls
        yield item




