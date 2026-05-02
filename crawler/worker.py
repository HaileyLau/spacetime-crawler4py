from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker-20")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp, self.frontier)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)

            # Update the log
            self.update_log()

            time.sleep(self.config.time_delay)


    # Updates the log after every URL that is scraped
    def update_log(self) -> None:

        with open("report2.txt", "w") as file:
                file.write("Assignment 2: Web Crawler Report\nZhengxing Chen | Hailey Lau | Wanrong Wu\n\n")

                file.write("Number of unique pages found: " + str(self.frontier.num_unique_urls) + "\n\n")

                file.write("The longest page found was: " + self.frontier.longest_page + " with " + str(self.frontier.longest_page_length) + " words.\n\n")
                
                file.write("The 50 most common words were:\n")
                self.write_most_common_words(self.frontier.word_counts, file)

                file.write("The subdomains found were:\n")
                self.write_subdomains(self.frontier.subdomains, file)

        
    # Helper function to print out the 50 most common stopwords in descending order
    def write_most_common_words(self, counts: dict[str, int], file) -> None:

        # Reorder by descending frequency first
        ordered_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))) # Suggested by ChatGPT

        counter = 0
        for key, value in ordered_counts.items():

            if counter == 50:
                break

            file.write("    " + key + " - " + str(value) + "\n")
            counter += 1

        file.write("\n")

    # Helper function to print out all subdomainds in alphabetic order
    def write_subdomains(self, subdomains: dict[str, int], file) -> None:

        # Order the subdomains alphabetically first
        ordered_subdomains = dict(sorted(subdomains.items()))

        for key, value in ordered_subdomains.items():

            file.write("    " + key + ", " + str(value) + "\n")

        file.write("\n")


            
