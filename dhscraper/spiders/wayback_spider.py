import scrapy
from dhscraper.items import DhscraperItem

class WaybackSpider(scrapy.Spider):
    """identify the spider"""
    name = "wayback_machine"
    allowed_domains = ["web.archive.org"] # too restrictive?
    start_urls = [
        "https://web.archive.org/web/20200619155607/https://dh2014.org/abstracts/",
    ]

    def parse(self, response):
        """
        handles the response downloaded for the request made for the start url
        """
        yield from response.follow_all(xpath="//*[@id='post-1064']/div/div/ul/li/a", callback=self.parse_abstract, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstracts
        """
        item = DhscraperItem()
        item["abstract"] = response.url
        item["origin"] = response.meta["start_url"]
        item["urls"] = {ref for ref in response.xpath("//p/a/@href|//p/*/a/@href").getall()}
        return item

