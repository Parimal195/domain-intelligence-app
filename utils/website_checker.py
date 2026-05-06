"""
Website Checker for the Domain Intelligence App.
Checks if a domain is actively used by a company or if it's parked/up for sale.
"""

import requests
import socket
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

def check_domain_status(record: Dict, timeout: int = 4) -> Dict:
    """
    Checks domain availability and parking status.
    Updates the record's 'availability_status'.
    """
    domain = record["domain"]
    
    # Fast check: Does it resolve to an IP?
    try:
        socket.gethostbyname(domain)
        # It resolves, so it's definitely registered (Taken or For Sale)
        is_registered = True
    except socket.gaierror:
        # Doesn't resolve. Could be available, or registered but inactive.
        # For our suggestion engine, we will rely on RDAP for definitive checks later, 
        # but if we are here, we can guess it's 'Available' if we can't do whois.
        # Let's default to Available if it doesn't resolve.
        record["availability_status"] = "✅ Available"
        return record
        
    if is_registered:
        url = f"http://{domain}"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            if resp.status_code == 200:
                text = resp.text.lower()
                for kw in PARKED_KEYWORDS:
                    if kw in text:
                        record["availability_status"] = "⚠️ For Sale"
                        return record
                        
            record["availability_status"] = "❌ Taken"
            return record
        except Exception:
            record["availability_status"] = "❌ Taken"
            return record

    return record

def validate_availability(domains: List[Dict], max_workers: int = 20) -> List[Dict]:
    """
    Validates a list of domain records, adding an 'availability_status' to each.
    """
    log.info(f"Validating availability for {len(domains)} domains...")
    validated = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_record = {
            executor.submit(check_domain_status, record): record 
            for record in domains
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_record):
            completed += 1
            try:
                validated.append(future.result())
            except Exception as e:
                record = future_to_record[future]
                record["availability_status"] = "❔ Unknown"
                validated.append(record)
                
            if completed % 100 == 0:
                log.info(f"  Validated {completed}/{len(domains)} domains.")
                
    return validated
