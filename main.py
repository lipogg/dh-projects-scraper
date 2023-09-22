from dhscraper.spiders.wayback_spider import WaybackSpider
from dhscraper.spiders.zenodo_spider import ZenodoSpider
from dhscraper.spiders.git_spider import GitSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
C
def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings) # same settings applied to all spiders
    #process.crawl(WaybackSpider)
    process.crawl(ZenodoSpider)
    #process.crawl(GitSpider)
    process.start()


if __name__ == '__main__':
    main()

