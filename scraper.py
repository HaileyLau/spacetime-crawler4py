import re
from urllib.parse import urlparse, urljoin, urlunparse

from bs4 import BeautifulSoup 


def scraper(url, resp):

    return extract_next_links(url, resp)

    # extract_next_link() already checks that a link is_desirable() before returning
        # links = extract_next_links(url, resp)
        # return [link for link in links if is_desirable(link)]


# Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
def extract_next_links(url, resp):
    try:
        # List to hold the scraped URLs (using a set for faster lookup)
        urls: set[str] = set()

        # Ensure that the page was successfully retrieved before attempting to parse it
        if resp.status != 200:
            
            # Print the error message before returning an empty list of URLs
            print("\nAN ERROR HAS OCCURRED")
            print(resp.error)
            print()

            return urls

        # BeautifulSoup converts the HTML response into an object that can be parsed by HTML tag
        text = BeautifulSoup(resp.raw_response.content, "html.parser")
    
        
        # Finds all tags that have an href attribute
        for tag in text.find_all(href=True):

            # Get the link from the href attribute
            link: str = tag.get("href")

            # skip empty links and nonhttp links
            if not link or link.startswith(("mailto:")) or link.startswith(("javascript:")):
                continue

            # parse real urls
            link = urljoin(url, link)

            # remove fragments
            parsed = urlparse(link)
            link = urlunparse(parsed._replace(fragment=""))

            # Add the link to the scraped URLS if it's desirable AND not a duplicate 
            if (is_desirable(link)) and (link not in urls):
                urls.add(link)

        return list(urls)
    
    except ValueError:
        print ("ValueError for ", url)
        return None
    
    except AssertionError:
        print ("AssertionError for ", url)
        return None

    except TypeError:
        print ("TypeError for ", url)
        raise


def is_desirable(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
        in_domain = False

        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check if url is in the allowed domains
        hostname = parsed.hostname
        if hostname:
            hostname = hostname.lower()
            for domain in domains:
                if hostname == domain or hostname.endswith("." + domain):
                    in_domain = True
        if not in_domain:
            return False
        
        # swiki pages seem to be the same as wiki pages
        subdomains = {"swiki", "dale-cooper-v0", ".lom."}
        for subdomain in subdomains:
            if subdomain in url.lower():
                return False
        
        # Check query for crawler traps
        trap_params = {"tribe", "orderby", "ical", "format=xml", "p=", "filter", "date=", "share=",
                        "page_id", "rest_route", "id=", "tab_files", "tab_details", "do=", "idx=",
                        "image=", "rev=", "rev2", "search=", "keywords=", "eventdisplay", "version=",
                        "precision=second"}
        query = parsed.query.lower()
        for param in trap_params:
            if param in query:
                return False
        
        # Check path for crawler traps
        path_segments = {"/wp-", "/feed", "xml", "/page", "/login", "/today", "/month", "/events/", "/index",
                         "/tsld", "/sld", "/list"}
        path = parsed.path.lower()
        for segment in path_segments:
            if segment in path:
                return False
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or re.search(r"\d{4}-\d{2}", path):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except ValueError:
        print ("ValueError for ", url)
        return False

    except TypeError:
        print ("TypeError for ", parsed)
        raise
