import scrapy
from dhscraper.items import DhscraperItem
from lxml import etree, html
import json
import logging
from ..utils import extract_urls


class GitSpider(scrapy.Spider):
    """identify the spider"""
    name = "github"
    allowed_domains = ["api.github.com", "raw.githubusercontent.com"]
    start_urls = [#"https://api.github.com/repos/ADHO/dh2016/contents/xml",
                  #"https://api.github.com/repos/ADHO/dh2015/contents/xml",
                  "https://api.github.com/repos/elliewix/DHAnalysis/contents/DH2014/abstracts",
                  #"https://api.github.com/repos/ADHO/data_dh2013/contents/source/tei",
                  #"https://api.github.com/repos/747/tei-to-pdf-dh2022/contents/input/files",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/long-papers",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/panels",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/plenaries",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/posters",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/short-papers",
                  #"https://api.github.com/repos/ADHO/dh2018/contents/xml/workshops",
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
        item["abstract"] = response.url
        xml_string = response.body
        urls = set()

        if "DH2014" in response.meta["start_url"]:
            root = html.fromstring(xml_string)
            tag, attr_name = ('a', 'href')
            body_elements = root.xpath('//*[contains(@xmlns, "http://www.tei-c.org/ns/1.0")]')
            body_element = body_elements[0] if body_elements else None
            logging.debug('Body element: %s', body_element)
        else:
            root = etree.fromstring(xml_string)
            tag, attr_name = ('ref', 'target')
            body_element = root.find('.//{http://www.tei-c.org/ns/1.0}body') # use root.xpath here as well?
            logging.debug('Body element: %s', body_element)
        if body_element is not None:
            # extract well-formed urls
            refs = root.findall(f'.//{{http://www.tei-c.org/ns/1.0}}{tag}') # refs = root.xpath(f'.//tei:{tag}', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}) - see if this solves the issua with 2013 abstract 300
            logging.debug('Ref elements found: %s', refs)
            wf_urls = {ref.attrib[attr_name] for ref in refs}
            urls.update(wf_urls)
            logging.debug('Attribute matches found: %s', urls)
            # catch malformed urls: Several urls are not <ref> element attributes, but plain text in <p>, <item> or <bibl> elements
            body_text = ''.join(body_element.itertext()) #   Error if except was called for body_element = ...
            mf_urls = extract_urls(body_text)
            logging.debug('String matches found: %s', mf_urls)
            urls.update(mf_urls)
        else: # 919, 894, 879, 867, 861, ...
            logging.error('No element with xmlns attribute found: Document potentially empty')
            item["notes"] = "Abstract missing"
        item["urls"] = urls
        yield item
