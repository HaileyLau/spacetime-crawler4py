import re
from urllib.parse import urlparse, urljoin, urlunparse

from bs4 import BeautifulSoup 

# Global state for exact duplication
seen_exact = set()
seen_simhash = []
SIMHASH_BITS = 64
HAMMING_THREADHOLD = 3
# Weighted checksum for exact duplicate detection
def checkSum(text):
    total = 0
    for i, ch in enumerate(text):
        total += (i+1) * ord(ch)
    return total % (2 ** 64)
# hash function to map each token to a 64 bit integer
def _djb2(token):
    h = 5381
    for ch in token:
        h = ((h << 5) + h) + ord(ch)
        h &= 0xFFFFFFFFFFFFFFFF # keep it 64 bit
    return h

# Split text into tokens from last assignment (but length > 2)
def tokenize(text):
    tokens = []
    curr = []
    for ch in text:
        if ch.isalnum():
            curr.append(ch.lower())
        else:
            if len(curr) > 2:
                tokens.append("".join(curr))
            curr = []
    if len(curr) > 2:
        tokens.append("".join(curr))
    return tokens

# Compute a 64 bit simhash fingerprint for the given text
def simHash(text):
    tokens = tokenize(text)
    if not tokens:
        return 0
    
    # For each bit position, count how many token hashes have that bit set vs unset
    v = [0] * SIMHASH_BITS
    for token in tokens:
        h = _djb2(token)
        for i in range(SIMHASH_BITS):
            if h & (1 << (SIMHASH_BITS - 1 - i)):
                v[i] += 1
            else:
                v[i] -= 1
    # If the count for a bit position, set that bit to 1
    fingerprint = 0
    for i in range(SIMHASH_BITS):
        if v[i] > 0:
            fingerprint |= (1 << (SIMHASH_BITS - 1 - i))

    return fingerprint
# count the number of differing bits betweeen two hashes
def hamming_distance(h1, h2):
    xor = h1 ^ h2
    count = 0
    while xor:
        xor &= xor - 1 # xor & xor -1 can remove the first 1 from right to left
        count += 1
    return count # count out how many differing numbers between two hashes
#Return true if the page is a exact duplication
def is_duplicate(text):
    # Filter low information webpages
    if not text or len(text.strip()) < 100:
        return True
    
    # Exact duplicate check by using checksum
    cs = checkSum(text)
    if cs in seen_exact:
        return True
    seen_exact.add(cs)

    # Near duplicate check
    sh = simHash(text)
    for (existing_sh,) in seen_simhash:
        if hamming_distance(sh, existing_sh) <= HAMMING_THREADHOLD:
            return True
    seen_simhash.append((sh,))

    return False

def scraper(url, resp):
    # Check that the response and its content are valid
    if not resp or resp.status != 200:
        return []
    if not resp.raw_response or not resp.raw_response.content:
        return []
    
    # Extract plain text from the HTML response
    text = BeautifulSoup(resp.raw_response.content, "html.parser")
    plain_text = text.get_text(separator=" ", strip=True)

    # Skip duplicate or near-duplicate pages
    if is_duplicate(plain_text):
        return []
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
        if not resp.raw_response or not resp.raw_response.content:
            return list(urls)
            

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
        return list(urls)
    
    except AssertionError:
        print ("AssertionError for ", url)
        return list(urls)

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
        trap_params = {"tribe", "orderby", "ical", "format=", "p=", "filter", "date=", "share=",
                        "page_id", "rest_route", "id=", "tab_files", "tab_details", "do=", "idx=",
                        "image=", "rev=", "rev2", "search=", "keywords=", "eventdisplay", "version=",
                        "precision=second", "C=", "action=", "people="}
        query = parsed.query.lower()
        for param in trap_params:
            if param in query:
                return False
        
        # Check path for crawler traps
        path_segments = {"/wp-", "/feed", "xml", "/page", "/login", "/today", "/month", "/events/", "/index",
                         "/tsld", "/sld", "/list", "/asterix/", "/admin", ":support"}
        path = parsed.path.lower()
        for segment in path_segments:
            if segment in path:
                return False
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or re.search(r"\d{4}-\d{2}", path):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|mpg"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|sdf|can|mol"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except ValueError as e:
        print ("ValueError for ", url)
        print ("Error: ", e)
        return False

    except TypeError as e:
        print ("TypeError for ", url)
        print ("Error: ", e)
        raise
