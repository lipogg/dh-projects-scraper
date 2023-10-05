import scrapy
from dhscraper.items import DhscraperItem
import xml.etree.ElementTree as ET
import json
import regex
import logging


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
                  ]

    def parse(self, response):
        """
        handles the response downloaded for each of the requests made
        """
        logging.info('Parse function called on %s', response.url)
        response_dict = json.loads(response.body)
        for item in response_dict:
            yield scrapy.Request(item["download_url"], callback=self.parse_abstract, meta={"start_url": response.url})

    def parse_abstract(self, response):
        """
        handles the response downloaded for each of the requests made: extracts links to dh projects from abstract xml files
        """
        item = DhscraperItem()
        logging.debug('DhscraperItem created')
        item["origin"] = response.meta["start_url"]
        xml_string = response.text
        root = ET.fromstring(xml_string)
        refs = root.findall('.//{http://www.tei-c.org/ns/1.0}ref')
        item["abstract"] = response.url
        try:
            item["urls"] = {ref.attrib['target'] for ref in refs}
        except KeyError:
            logging.error('Ref element does not have a target attribute.')
        # catch malformed urls: Several urls are not <ref> element attributes, but plain text in <p> elements
        url_pattern = (
            r"(https?://)?"  # matches optional "http://" or "https://"
            r"(www\.)?"  # matches optional "www."            
            r"[-a-zA-Z0-9@:%._\+~#=]{1,256}"  # matches main part of the domain name 
            r"(?:-[\r\n]{0,4}[-a-zA-Z0-9@:%._\+~#=]{1,256})?"  # matches possible line breaks and the continuation of the domain or path, "-" to exclude overmatching in cases such as via\nraganwald.com 
            r"(?:\.[a-zA-Z0-9()]{1,6}\b)+?"  # matches the TLD and possible SLDs, non-greedy quantifier to reduce backtracking
            r"(?:[\r\n]{0,4}[-a-zA-Z0-9()@:%_\+.~#?&//=]{1,256})?"  # matches possible line breaks and the continuation of the path or query params, anchors etc
        )
        logging.debug('URL pattern: %s', url_pattern)
        body_element = root.find('.//{http://www.tei-c.org/ns/1.0}body')
        body_text = ''.join(body_element.itertext())
        try:
            mf_urls = {match.group() for match in regex.finditer(url_pattern, body_text, timeout=20)} #f"{p_text} {bibl_text}"
            logging.debug('Matches found: %s', mf_urls)
            item["urls"].update(mf_urls)
        except regex.TimeoutError:
            logging.error('Regex timed out on %s', response.url)
        yield item
