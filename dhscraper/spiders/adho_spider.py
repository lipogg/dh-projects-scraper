import scrapy
from dhscraper.items import DhscraperItem
import re

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
        yield from response.follow_all(xpath="//*[@id='tablepress-9']/tbody/tr/td/a", callback=self.parse_abstract, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract web pages
        """
        item = DhscraperItem()
        item["abstract"] = response.url
        item["origin"] = response.meta["start_url"]
        pattern = r"(?<!mailto:)(https?://)?(www\.)?[-a-zA-Z0-9@:%._\+~#=\n]{1,256}\.[a-zA-Z0-9()\n]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=\n]*)"
        abstract = response.xpath("//*[@id='index.xml-body.1_div.1']").get()
        item["urls"] = {match.group() for match in re.finditer(pattern, abstract)}
        return item


