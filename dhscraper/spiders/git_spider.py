import scrapy
from dhscraper.items import DhscraperItem
import xml.etree.ElementTree as ET
import json
import fitz
import re
import io

class GitSpider(scrapy.Spider):
    """identify the spider"""
    name = "github"
    allowed_domains = ["api.github.com", "raw.githubusercontent.com"]
    start_urls = ["https://api.github.com/repos/ADHO/dh2016/contents/xml",
                  "https://api.github.com/repos/ADHO/dh2015/contents/xml",
                  "https://api.github.com/repos/ADHO/data_dh2013/contents/source/tei",
                  "https://api.github.com/repos/747/tei-to-pdf-dh2022/contents/input/files",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/long-papers",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/panels",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/plenaries",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/posters",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/short-papers",
                  "https://api.github.com/repos/ADHO/dh2018/contents/xml/workshops",
                  "https://api.github.com/repos/ADHO/dh2017/contents/pdf",
                  ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        response_dict = json.loads(response.body)  # .text
        for item in response_dict:
            yield scrapy.Request(item["download_url"], callback=self.parse_abstract)

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract xml files
        """
        item = DhscraperItem()
        if response.url.endswith(".pdf"):
            item["origin"] = response.url
            filestream = io.BytesIO(response.body)
            pdf = fitz.open(stream=filestream, filetype="pdf")
            pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=\n]{1,256}\.[a-zA-Z0-9()\n]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=\n]*)"
            text = chr(12).join([page.get_text(flags=16) for page in pdf])
            item["urls"] = [match.group() for match in re.finditer(pattern, text)]
        else:
            xml_string = response.text
            root = ET.fromstring(xml_string)
            refs = root.findall('.//{http://www.tei-c.org/ns/1.0}ref')
            item["origin"] = response.url
            item["urls"] = [ref.attrib['target'] for ref in refs]
        return item
