from scrapy.spiders import XMLFeedSpider
from dhscraper.items import DhscraperItem

# comment out ROBOTSTXT_OBEY = True in settings.py to run this spider
class ZenodoSpider(XMLFeedSpider):
    """identify the spider"""
    name = "zenodo"
    allowed_domains = ["zenodo.org"]
    start_urls = [
        "https://zenodo.org/api/files/d2da19c6-7b4e-42d1-86dd-d959724ca851/DH2023_BookOfAbstracts.xml",
    ]
    namespaces = [('tei', 'http://www.tei-c.org/ns/1.0')]
    iterator = "iternodes"
    itertag = "ref"

    def parse_node(self, response, node):
        """
        handles the response downloaded for the request made for the start url
        """
        item = DhscraperItem()
        item["urls"] = node.attrib['target']
        item["origin"] = response.url
        return item




