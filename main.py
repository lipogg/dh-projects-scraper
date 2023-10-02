from dhscraper.spiders.wayback_spider import WaybackSpider
from dhscraper.spiders.zenodo_xml_spider import ZenodoXMLSpider
from dhscraper.spiders.zenodo_txt_spider import ZenodoTXTSpider
from dhscraper.spiders.git_spider import GitSpider
from dhscraper.spiders.dataverse_spider import DataverseSpider
from dhscraper.spiders.adho_spider import AdhoSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings)  # same settings applied to all spiders
    process.crawl(AdhoSpider)
    process.crawl(ZenodoXMLSpider)
    process.crawl(ZenodoTXTSpider)
    process.crawl(DataverseSpider)
    process.crawl(GitSpider)
    process.crawl(WaybackSpider)
    process.start()


if __name__ == '__main__':
    main()

