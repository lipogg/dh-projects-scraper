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
        if len(adapter["urls"]) > 0:
            self.process_urls(adapter)
            self.get_path_length(adapter)
        return item

    def extract_year(self, adapter):
        pattern_year = r'dh(\d{4})'
        adapter["year"] = re.search(pattern_year, adapter["origin"], re.IGNORECASE).group(1)

    def process_urls(self, adapter):
        exclude_domains = ["doi", "tei-c", "w3", "wikipedia", "wikidata", "orcid",
                           "cidoc-crm", "jstor", "zotero", "researchgate", "gephi",
                           "zenodo", "culturalanalytics", "nature", "medium", "twitter",
                           "reddit", "arxiv", "journalofdigitalhumanities", "youtube",
                           "theguardian", "sciencedirect", "archives-ouvertes"]
        exclude_subdomains = ["journals"]
        adapter["urls"] = list(adapter["urls"])  # convert set to list
        pattern_end = r'[\./\):]+$|(\-?\n)|\s|\([^)]+$|\((A|accessed).*|\s*$'  # match any combination of /, ), : and . or open brackets at the end of a sentence, \n and -\n anywhere, with trailing whitespace
        valid_urls = []
        for url in adapter["urls"]:
            cleaned_url = re.sub(pattern_end, "", url)
            url_parts = extract(cleaned_url)
            if (
                    url_parts.domain.lower() not in exclude_domains
                    and url_parts.subdomain.lower() not in exclude_subdomains
                    and not cleaned_url.endswith((".pdf", ".xml", ".jpg", ".jpeg", ".png", ".md", ".txt", ".zip"))
                    and not cleaned_url.startswith("mailto")
                    and url_parts.suffix  # validate url: suffix is empty string if invalid
                    and not validators.email(cleaned_url)  # exclude email addresses not preceded by mailto scheme
            ):
                valid_urls.append(cleaned_url)
        adapter["urls"] = valid_urls

    def get_path_length(self, adapter):
        adapter["path_length"] = []
        for url in adapter["urls"]:
            url_path = urlparse(url).path
            adapter["path_length"].append(len(re.findall("/", url_path)))


class DuplicatesPipeline:
    """Looks for duplicate items based on URL and year, and drops those items that were already processed.
    Duplicate entries are removed when they occur within the Book of Abstracts for a specific conference.
    However, if similar entries appear across the Books of Abstracts from different conferences,
    they are not considered duplicates and are retained.

    Adapted from @ref: https://docs.scrapy.org/en/latest/topics/item-pipeline.html#duplicates-filter
    """
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        year = adapter["year"]
        unique_urls = []
        for url in adapter["urls"]:
            url_year = (url, year)
            if url_year not in self.urls_seen:
                self.urls_seen.add(url_year)
                unique_urls.append(url)
        adapter["urls"] = unique_urls
        return item


class GoogleSheetsPipeline:
    def __init__(self):
        gc = gspread.service_account(filename="./creds.json")
        self.sh = gc.open("DH Projects").sheet1
        self.rows = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        num_urls = len(adapter["urls"])
        if num_urls > 0:
            for i in range(num_urls):
                row = [adapter["year"], adapter["origin"], adapter["abstract"], adapter["path_length"][i], adapter["urls"][i], adapter.get("notes", ""), adapter["http_status"]]
                self.rows.append(row)
        else:
            row = [adapter["year"], adapter["origin"], adapter["abstract"], "NaN", "NaN", adapter.get("notes", ""), adapter["http_status"]]
            self.rows.append(row)
        return item

    def close_spider(self, spider):
        header = ["Year", "Origin", "Abstract", "Path Length", "Project Url", "Notes", "HTTP Status"]
        if len(self.sh.get_all_values()) == 0:  # this is not working! is None?
            self.sh.append_row(header)
        self.sh.append_rows(self.rows)
