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
        #item["urls"] = {match.group() for match in re.finditer(url_pattern, abstract)}
        item["urls"] = set()
        for match in re.finditer(url_pattern, abstract):
            url = match.group()
            if url.endswith(("-", "_")):
                # Start position after url match
                start_pos = match.end()
                subsequent_text = abstract[start_pos:]
                # Pattern for a line break followed by spaces and a URL path
                end_url_pattern = r"[\r\n\s]+([-a-zA-Z0-9@:%._\+~#=]{1,256})"
                end_match = re.search(end_url_pattern, subsequent_text)
                # If there is a match, concatenate with the original URL
                if end_match:
                    url_end = end_match.group(1)
                    url = url + url_end
            item["urls"].add(url)
        item["abstract"] = "n.a."
        yield item





