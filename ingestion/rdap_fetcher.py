"""
RDAP Domain Expiry Fetcher for the Domain Intelligence App.

Queries the public RDAP protocol to retrieve domain registration
and expiry data. Handles rate limiting, retries, and graceful failures.
"""

import time
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List

from utils.config import (
    RDAP_BASE_URL,
    RDAP_RATE_LIMIT_SECONDS,
    RDAP_MAX_RETRIES,
    RDAP_TIMEOUT_SECONDS,
)
from utils.helpers import (
    is_valid_domain,
    extract_tld,
    extract_sld,
    parse_date,
    retry_with_backoff,
)
from utils.logger import get_logger

log = get_logger(__name__)


class RDAPFetcher:
    """
    Fetches domain expiry information via the RDAP protocol.
    
    RDAP (Registration Data Access Protocol) is the modern replacement
    for WHOIS, providing structured JSON responses.
    """

    def __init__(self):
        self.base_url = RDAP_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/rdap+json",
            "User-Agent": "DomainIntelligenceApp/1.0 (research; github.com)",
        })
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RDAP_RATE_LIMIT_SECONDS:
            sleep_time = RDAP_RATE_LIMIT_SECONDS - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _extract_expiry_from_rdap(self, data: dict) -> Optional[str]:
        """
        Extract expiration date from RDAP JSON response.
        
        Checks multiple possible locations in the RDAP response structure.
        """
        # Method 1: Direct events array
        events = data.get("events", [])
        for event in events:
            if event.get("eventAction") == "expiration":
                return event.get("eventDate")

        # Method 2: Check in entities
        entities = data.get("entities", [])
        for entity in entities:
            for event in entity.get("events", []):
                if event.get("eventAction") == "expiration":
                    return event.get("eventDate")

        # Method 3: Check for 'registrationExpiry' in notices
        notices = data.get("notices", [])
        for notice in notices:
            title = notice.get("title", "").lower()
            if "expir" in title:
                desc = notice.get("description", [])
                if desc:
                    return desc[0]

        return None

    def _extract_registrar(self, data: dict) -> str:
        """Extract registrar name from RDAP response."""
        entities = data.get("entities", [])
        for entity in entities:
            roles = entity.get("roles", [])
            if "registrar" in roles:
                # Try vcardArray first
                vcard = entity.get("vcardArray", [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == "fn":
                            return item[3]
                # Fallback to handle
                handle = entity.get("handle", "")
                if handle:
                    return handle
        return "Unknown"

    def _extract_country(self, data: dict) -> str:
        """Extract registrant/registrar country from RDAP response."""
        entities = data.get("entities", [])
        for entity in entities:
            roles = entity.get("roles", [])
            if "registrar" in roles or "registrant" in roles:
                vcard = entity.get("vcardArray", [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == "adr":
                            # adr is typically a list. Country is usually at index 6 or the last element in the value array.
                            if len(item) > 3 and isinstance(item[3], list) and len(item[3]) >= 7:
                                country = item[3][6]
                                if country: return country
        return "Unknown"

    @retry_with_backoff(
        max_retries=RDAP_MAX_RETRIES,
        base_delay=2.0,
        exceptions=(requests.RequestException,),
    )
    def fetch_domain(self, domain: str) -> Optional[Dict]:
        """
        Fetch expiry data for a single domain via RDAP.
        
        Args:
            domain: Domain name to query (e.g., 'example.com').
        
        Returns:
            Dict with domain info or None if unavailable.
        """
        if not is_valid_domain(domain):
            log.warning(f"Invalid domain format: {domain}")
            return None

        self._rate_limit()

        url = f"{self.base_url}{domain}"

        try:
            response = self.session.get(url, timeout=RDAP_TIMEOUT_SECONDS)

            if response.status_code == 404:
                # 404 means the domain is unregistered!
                return {
                    "domain": domain,
                    "tld": extract_tld(domain),
                    "sld": extract_sld(domain),
                    "availability_status": "✅ Available",
                    "registrar": "N/A",
                    "country": "Unknown",
                    "source": "rdap",
                    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                }

            if response.status_code == 429:
                log.warning(f"RDAP rate limited for {domain}")
                time.sleep(5)  # Extra backoff for rate limit
                raise requests.RequestException("Rate limited")

            response.raise_for_status()
            data = response.json()

            registrar = self._extract_registrar(data)
            country = self._extract_country(data)

            # If RDAP returns 200 OK, the domain is registered
            return {
                "domain": domain,
                "tld": extract_tld(domain),
                "sld": extract_sld(domain),
                "availability_status": "❌ Taken", # Validated further later
                "registrar": registrar,
                "country": country,
                "source": "rdap",
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }

        except requests.Timeout:
            log.warning(f"RDAP timeout for {domain}")
            raise
        except requests.RequestException as e:
            log.warning(f"RDAP request failed for {domain}: {e}")
            raise

    def fetch_batch(self, domains: List[str], max_count: int = 100) -> List[Dict]:
        """
        Fetch expiry data for a batch of domains.
        
        Args:
            domains: List of domain names.
            max_count: Maximum domains to query (rate limit protection).
        
        Returns:
            List of successfully fetched domain records.
        """
        results = []
        domains = domains[:max_count]

        log.info(f"RDAP batch fetch: {len(domains)} domains")

        for i, domain in enumerate(domains):
            try:
                result = self.fetch_domain(domain)
                if result:
                    results.append(result)
                    log.debug(f"[{i+1}/{len(domains)}] Fetched: {domain}")
            except Exception as e:
                log.warning(f"[{i+1}/{len(domains)}] Failed: {domain} — {e}")
                continue

        log.info(f"RDAP batch complete: {len(results)}/{len(domains)} successful")
        return results


if __name__ == "__main__":
    fetcher = RDAPFetcher()
    # Test with a known domain
    result = fetcher.fetch_domain("google.com")
    if result:
        print(f"Domain: {result['domain']}")
        print(f"Expiry: {result['expiry_date']}")
        print(f"Registrar: {result.get('registrar', 'N/A')}")
    else:
        print("No result found")
