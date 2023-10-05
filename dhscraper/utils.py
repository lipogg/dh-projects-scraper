from .constants import URL_PATTERN, PATH_PATTERN
import regex
import logging


def extract_urls(abstract):
    logging.debug('URL pattern: %s', URL_PATTERN)
    extracted_urls = set()

    try:
        for url_match in regex.finditer(URL_PATTERN, abstract, timeout=20):
            logging.debug('Match found: %s', url_match.group())
            url = url_match.group()
            start_pos = url_match.end()
            # catch continuation of the path if split across lines, Zenodo test case mw2013.museumsandtheweb.com/...; Adho test cases http://digital.law.washington.edu/dspace-, http://www.californialawreview.org/wp-, propublica.org
            while url.endswith(("-", "_", "–")):
                logging.debug('URL ends with "-", "_", or "–": %s', url)
                subsequent_text = abstract[start_pos:]
                path_match = regex.search(PATH_PATTERN, subsequent_text)
                if path_match:
                    logging.debug('End match found: %s', path_match.group(1))
                    url_end = path_match.group(1)
                    url += url_end
                    start_pos += len(url_end)
                else:
                    break

            extracted_urls.add(url)
    except regex.TimeoutError:
        logging.error('Regex timed out while processing abstract.')

    return extracted_urls
