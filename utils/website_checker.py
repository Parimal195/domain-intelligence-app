"""
Website Checker for the Domain Intelligence App.
Checks if a domain is actively used by a company or if it's parked/up for sale.
"""

import requests
import concurrent.futures
from typing import List, Dict

from utils.logger import get_logger

log = get_logger(__name__)

# Keywords indicating a domain is parked or up for sale
PARKED_KEYWORDS = [
    "domain is for sale", "buy this domain", "is available for purchase",
    "parked free", "sedo.com", "dan.com", "hugedomains", "domain name is for sale",
    "inquire about this domain", "this domain may be for sale", "make an offer",
    "purchase this domain", "domain is available", "submit your offer",
    "spaceship.com", "godaddy.com/forsale", "afternic", "domain seller",
    "this domain is listed for sale", "buyer protection program", "buy it now",
    "contact owner", "minimum offer", "domain broker", "domain name is available",
    "get this domain", "own this domain", "sale price", "buy now for",
    "this webpage is parked", "this site is parked", "domain parking",
    "buy domain", "domains for sale", "acquire this domain"
]

def is_domain_in_use(domain: str, timeout: int = 4) -> bool:
    """
    Checks if a domain is actively in use by a company.
    Returns True if the site responds with 200 OK and is NOT a parking page.
    Returns False if it times out, fails to resolve, or is parked.
    """
    url = f"http://{domain}"
    try:
        # Use headers to act like a normal browser and avoid basic blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # If we didn't get a successful response, it's not an active company site
        if resp.status_code != 200:
            return False
            
        text = resp.text.lower()
        
        # Check for parked keywords
        for kw in PARKED_KEYWORDS:
            if kw in text:
                return False
                
        # If it responded 200 and isn't parked, we assume it's in use
        return True
        
    except Exception:
        # DNS failure, timeout, connection refused, etc. 
        # If it doesn't resolve or time out, it's not an active company site.
        return False

def filter_in_use_domains(domains: List[Dict], max_workers: int = 15) -> List[Dict]:
    """
    Filters a list of domain records, keeping only those that are actively in use.
    Uses multithreading to speed up the network requests.
    """
    log.info(f"Checking {len(domains)} domains to see if they are actively in use...")
    active_domains = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a mapping of future to domain record
        future_to_record = {
            executor.submit(is_domain_in_use, record["domain"]): record 
            for record in domains
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_record):
            record = future_to_record[future]
            completed += 1
            
            try:
                is_active = future.result()
                if is_active:
                    active_domains.append(record)
            except Exception as e:
                log.debug(f"Error checking {record['domain']}: {e}")
                
            if completed % 50 == 0:
                log.info(f"  Checked {completed}/{len(domains)} domains. Found {len(active_domains)} active so far.")
                
    log.info(f"Filtering complete. Kept {len(active_domains)}/{len(domains)} domains that are in use.")
    return active_domains
