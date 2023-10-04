import scrapy
from dhscraper.items import DhscraperItem
import logging
import regex

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
        logging.info('Parse function called on %s', response.url)
        item = DhscraperItem()
        logging.debug('DhscraperItem created')
        item["origin"] = response.url
        url_pattern = (
            r"(https?://)?"  # matches optional "http://" or "https://"
            r"(www\.)?"  # matches optional "www."            
            r"[-a-zA-Z0-9@:%._\+~#=]{1,256}"  # matches main part of the domain name 
            r"(?:-[\r\n]{0,4}[-a-zA-Z0-9@:%._\+~#=]{1,256})?"  # matches possible line breaks and the continuation of the domain or path, "-" to exclude overmatching in cases such as via\nraganwald.com 
            r"(?:\.[a-zA-Z0-9()]{1,6}\b)+?"   # matches the TLD and possible SLDs, non-greedy quantifier to reduce backtracking
            r"(?:[\r\n]{0,4}[-a-zA-Z0-9()@:%_\+.~#?&//=]{1,256})?"  # matches possible line breaks and the continuation of the path or query params, anchors etc
        )
        logging.debug('URL pattern: %s', url_pattern)
        abstract = response.text
        item["urls"] = set()
        end_url_pattern = r"[\r\n\s]+([-a-zA-Z0-9@:%._\+~#=/]{1,256})"
        try:
            for match in regex.finditer(url_pattern, abstract, timeout=20):
                logging.debug('Match found: %s', match.group())
                url = match.group()
                start_pos = match.end()
                # catch continuation of the path if split across lines, test case mw2013.museumsandtheweb.com/...
                while url.endswith(("-", "_", "–")):
                    logging.debug('URL ends with "-", "_", or "–": %s', url)
                    subsequent_text = abstract[start_pos:]
                    end_match = regex.search(end_url_pattern, subsequent_text)
                    if end_match:
                        logging.debug('End match found: %s', end_match.group(1))
                        url_end = end_match.group(1)
                        url += url_end
                        start_pos += len(url_end)
                    else:
                        break
                item["urls"].add(url)
        except regex.TimeoutError:
            logging.error('Regex timed out on %s', response.url)
        item["abstract"] = "n.a."
        logging.info('Item ready to be yielded')
        yield item





