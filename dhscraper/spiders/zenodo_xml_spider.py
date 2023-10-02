from scrapy.spiders import XMLFeedSpider
from dhscraper.items import DhscraperItem


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
        item["urls"] = set(node.xpath('.//ref/@target', namespaces=self.namespaces).getall())
        yield item




