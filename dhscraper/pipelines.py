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
import logging


class DhscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.extract_year(adapter)
        if len(adapter["urls"]) > 0:
            self.process_urls(adapter)
        return item

    def extract_year(self, adapter):
        pattern_year = r"dh(\d{4})"
        adapter["year"] = re.search(
            pattern_year, adapter["origin"], re.IGNORECASE
        ).group(1)

    def process_urls(self, adapter):
        exclude_domains = [
            "doi",
            "tei-c",
            "w3",
            "wikipedia",
            "wikidata",
            "orcid",
            "cidoc-crm",
            "jstor",
            "zotero",
            "researchgate",
            "gephi",
            "zenodo",
            "culturalanalytics",
            "nature",
            "medium",
            "twitter",
            "reddit",
            "arxiv",
            "journalofdigitalhumanities",
            "youtube",
            "theguardian",
            "sciencedirect",
            "archives-ouvertes",
        ]
        exclude_subdomains = ["journals"]
        adapter["urls"] = list(adapter["urls"])  # convert set to list
        pattern_end = r"[\./\):]+$|\([^)]+$|/?\((A|accessed).*|\s*$"  # match any combination of /, ), : and . or open brackets, (Accessed or /(Accessed at the end of a sentence, and any trailing whitespace
        pattern_newline = r"(\-?(\n|\r)|\s)"  # match \n or \r optionally preceded by -, and whitespace anywhere in the url
        pattern_start = (
            r"^.*?http"  # lazy match any characters before the first occurrence of http
        )
        valid_urls = []

        for url in adapter["urls"]:
            logging.debug("Current URL is: %s", url)
            pre_cleaned_url = re.sub(pattern_end, "", url)
            cleaned_url = re.sub(
                pattern_start, "http", pre_cleaned_url
            )  # flags=re.IGNORECASE
            newline_free_url = re.sub(pattern_newline, "", cleaned_url)
            url_parts = extract(newline_free_url)
            suffix = url_parts.suffix  # returns "" if no suffix is found
            if not suffix:  # kein Suffix gefunden
                matches = list(re.finditer(pattern_newline, cleaned_url))
                logging.debug("No suffix found in URL: %s", newline_free_url)
                logging.debug(
                    f"Found {len(matches)} newline characters in URL {cleaned_url}: {matches}"
                )
                while not suffix and len(matches) > 0:
                    logging.debug("While loop initiated for: %s", newline_free_url)
                    # Get and remove the last match
                    last_match = matches.pop()
                    # Remove everything after the last match
                    cleaned_url = cleaned_url[: last_match.start()]
                    # Update variables url_parts, suffix and newline_free_url
                    newline_free_url = re.sub(pattern_newline, "", cleaned_url)
                    logging.debug("Searching suffix for new URL: %s", newline_free_url)
                    url_parts = extract(newline_free_url)
                    suffix = url_parts.suffix
                    if suffix:
                        logging.debug(
                            "Suffix found in URL after removal: %s", newline_free_url
                        )
                        break
                    else:
                        logging.debug(
                            "No suffix found in URL after removal: %s", newline_free_url
                        )
            else:  # Suffix gefunden
                logging.debug("Suffix found in URL: %s", newline_free_url)

            if (
                url_parts.domain.lower() not in exclude_domains
                and url_parts.subdomain.lower() not in exclude_subdomains
                and not newline_free_url.endswith(
                    (".pdf", ".xml", ".jpg", ".jpeg", ".png", ".md", ".txt", ".zip")
                )
                and not newline_free_url.startswith("mailto")
                and url_parts.suffix  # validate url: suffix is empty string if invalid
                and not validators.email(
                    newline_free_url
                )  # exclude email addresses not preceded by mailto scheme
            ):
                valid_urls.append(newline_free_url)
                logging.debug("URL valid: %s", newline_free_url)
        logging.debug(
            "Cleaned or filtered out URLs: %s",
            list(set(adapter["urls"]) - set(valid_urls)),
        )
        adapter["urls"] = valid_urls


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
        logging.debug(
            "Duplicates removed: %s", list(set(adapter["urls"]) - set(unique_urls))
        )
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
                row = [
                    adapter["year"],
                    adapter["origin"],
                    adapter["abstract"],
                    adapter["urls"][i],
                    adapter.get("notes", ""),
                    adapter["http_status"],
                ]
                self.rows.append(row)
        else:
            row = [
                adapter["year"],
                adapter["origin"],
                adapter["abstract"],
                "NaN",
                adapter.get("notes", ""),
                adapter["http_status"],
            ]
            self.rows.append(row)
        return item

    def close_spider(self, spider):
        header = ["Year", "Origin", "Abstract", "Project Url", "Notes", "HTTP Status"]
        if len(self.sh.get_all_values()) == 0:
            self.sh.append_row(header)
        logging.debug(f"Appended {len(self.rows)} rows to Google Sheets.")
        self.sh.append_rows(self.rows)
