import scrapy
from dhscraper.items import DhscraperItem
import json
import fitz
import io

class DataverseSpider(scrapy.Spider):
    """identify the spider"""
    name = "dataverse"
    allowed_domains = ["dataverse.nl"]
    start_urls = [
        "https://dataverse.nl/api/search?q=.pdf&subtree=dh2019&per_page=1000",
                  ]
    custom_settings = {'ROBOTSTXT_OBEY': False,
                       'DOWNLOAD_DELAY': 10
                       }

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        response_dict = json.loads(response.body)  # .text
        for item in response_dict["data"]["items"]:
            yield scrapy.Request(item["url"], callback=self.parse_abstract)

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract xml files
        """
        item = DhscraperItem()
        item["origin"] = response.url
        filestream = io.BytesIO(response.body)
        pdf = fitz.open(stream=filestream, filetype="pdf")
        item["urls"] = {elem['uri'] for page in pdf for elem in page.get_links() if 'uri' in elem} # set comprehension to remove duplicates derived from malformatted hyperlinks
        return item
