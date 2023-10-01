# Item pipeline definitions
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import gspread
import re
from itemadapter import ItemAdapter
from tldextract import extract
from urllib.parse import urlparse
import validators


class DhscraperPipeline:

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.extract_year(adapter)
        self.process_urls(adapter)
        self.get_path_length(adapter)
        return item

    def extract_year(self, adapter):
        pattern_year = r'dh(\d{4})'
        adapter["year"] = re.search(pattern_year, adapter["origin"], re.IGNORECASE).group(1)

    def process_urls(self, adapter):
        exclude_domains = ["doi", "tei-c", "w3", "wikipedia", "wikidata", "orcid",
                           "cidoc-crm", "jstor", "zotero", "researchgate", "gephi",
                           "zenodo", "culturalanalytics", "nature", "medium",
                           "reddit", "arxiv", "journalofdigitalhumanities",
                           "theguardian", "sciencedirect", "archives-ouvertes"]
        exclude_subdomains = ["journals"]
        adapter["urls"] = list(adapter["urls"])  # convert set to list
        pattern_end = r'[\./\):]+$|(\-?\n)|\([^)]+$|\((A|accessed).*|\s*$'  # match any combination of /, ), : and . or open brackets at the end of a sentence, \n and -\n anywhere, with trailing whitespace
        valid_urls = []
        for url in adapter["urls"]:
            cleaned_url = re.sub(pattern_end, "", url)
            url_parts = extract(cleaned_url)
            if (
                    url_parts.domain not in exclude_domains
                    and url_parts.subdomain not in exclude_subdomains
                    and not cleaned_url.endswith((".pdf", ".xml", ".jpg", ".jpeg", ".png"))
                    and url_parts.suffix # validate url: suffix is empty string if invalid
                    and not validators.email(cleaned_url) # exclude email addresses
            ):
                valid_urls.append(cleaned_url)
        adapter["urls"] = valid_urls

    def get_path_length(self, adapter):
        adapter["path_length"] = []
        for url in adapter["urls"]:
            url_path = urlparse(url).path
            adapter["path_length"].append(len(re.findall("/", url_path)))


class DuplicatesPipeline:
    """Looks for duplicate items, and drops those items that were already processed

    @ref: https://docs.scrapy.org/en/latest/topics/item-pipeline.html#duplicates-filter
    """
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        unique_urls = []
        for url in adapter["urls"]:
            if url not in self.urls_seen:
                self.urls_seen.add(url)
                unique_urls.append(url)
        adapter["urls"] = unique_urls
        return item


class GoogleSheetsPipeline:
    def __init__(self):
        gc = gspread.service_account(filename="./creds.json")
        self.sh = gc.open("DH Projects").sheet1
        header = ["Year", "Origin", "Abstract", "Path Length", "Project Url"]
        self.rows = [header] if self.sh.acell("A1").value is None else []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for i in range(len(adapter["urls"])):
            row = [adapter["year"], adapter["origin"], adapter["abstract"], adapter["path_length"][i], adapter["urls"][i]]
            self.rows.append(row)
        return item

    def close_spider(self, spider):
        self.sh.append_rows(self.rows)
