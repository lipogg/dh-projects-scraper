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
                  #"https://api.github.com/repos/ADHO/dh2015/contents/xml",
                  #"https://api.github.com/repos/ADHO/data_dh2013/contents/source/tei",
                  #"https://api.github.com/repos/747/tei-to-pdf-dh2022/contents/input/files",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/long-papers",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/panels",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/plenaries",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/posters",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/short-papers",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/workshops",
                  #"https://api.github.com/repos/ADHO/dh2017/contents/pdf",
                  ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        response_dict = json.loads(response.body)
        for item in response_dict:
            yield scrapy.Request(item["download_url"], callback=self.parse_abstract, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract xml files
        """
        item = DhscraperItem()
        item["origin"] = response.meta["start_url"]
        pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=\n]{1,256}\.[a-zA-Z0-9()\n]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=\n]*)"
        if response.url.endswith(".pdf"):
            item["abstract"] = response.url
            filestream = io.BytesIO(response.body)
            pdf = fitz.open(stream=filestream, filetype="pdf")
            text = chr(12).join([page.get_text(flags=16) for page in pdf])
            item["urls"] = [match.group() for match in re.finditer(pattern, text)]
        else:
            xml_string = response.text
            root = ET.fromstring(xml_string)
            refs = root.findall('.//{http://www.tei-c.org/ns/1.0}ref')
            item["abstract"] = response.url
            item["urls"] = [ref.attrib['target'] for ref in refs]
            # catch malformatted urls: Several urls are not <ref> elements, but plain text
            p_text = ' '.join([p.text for p in root.findall('.//{http://www.tei-c.org/ns/1.0}p') if p.text])
            bibl_text = ' '.join([bibl.text for bibl in root.findall('.//{http://www.tei-c.org/ns/1.0}bibl') if bibl.text])
            mf_urls = [match.group() for match in re.finditer(pattern, f"{p_text} {bibl_text}")]
            item["urls"].extend(mf_urls)
        return item
