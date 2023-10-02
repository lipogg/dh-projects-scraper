import scrapy
from dhscraper.items import DhscraperItem
import re


class ZenodoTXTSpider(scrapy.Spider):
    """identify the spider"""
    name = "zenodo_txt"
    allowed_domains = ["zenodo.org"]
    start_urls = [
        "https://zenodo.org/record/1403230/files/dh2017.txt",
    ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        item = DhscraperItem()
        item["origin"] = response.url
        url_pattern = r"(https?://)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.(?:[a-zA-Z0-9()]{1,6}\b)(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"  # match emails here and exclude later to prevent accidentally matching email domains
        abstract = response.text
        item["urls"] = {match.group() for match in re.finditer(url_pattern, abstract)}
        item["abstract"] = "n.a."
        yield item





