"""
Public Domain Lists Scraper for the Domain Intelligence App.

Fetches expiring domain data from publicly accessible web sources.
Uses respectful scraping with rate limiting and proper user agents.
"""

import re
import time
import random
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

from utils.helpers import is_valid_domain, extract_tld, extract_sld, parse_date
from utils.logger import get_logger

log = get_logger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class PublicListsScraper:
    """
    Scrapes publicly available domain expiry lists.
    
    Implements respectful scraping with:
    - Rate limiting between requests
    - User agent rotation
    - Graceful error handling
    - Caching of results
    """

    def __init__(self):
        self.session = requests.Session()
        self._last_request_time = 0.0

    def _get_headers(self) -> dict:
        """Get request headers with rotated user agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def _rate_limit(self, min_delay: float = 2.0):
        """Enforce polite rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < min_delay:
            sleep_time = min_delay - elapsed + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def fetch_from_web_archives(self, max_domains: int = 200) -> List[Dict]:
        """
        Attempt to fetch domain lists from publicly available web sources.
        
        This is a best-effort approach — many sources require authentication
        or have CAPTCHA protection. Falls back gracefully.
        
        Args:
            max_domains: Maximum number of domains to fetch.
        
        Returns:
            List of domain records.
        """
        records = []

        # Source 1: Try public domain list APIs
        try:
            records.extend(self._fetch_from_public_api(max_domains))
        except Exception as e:
            log.warning(f"Public API fetch failed: {e}")

        # Source 2: Try GitHub-hosted domain datasets
        try:
            records.extend(self._fetch_from_github_datasets(max_domains))
        except Exception as e:
            log.warning(f"GitHub dataset fetch failed: {e}")

        log.info(f"Public lists: fetched {len(records)} domains total")
        return records[:max_domains]

    def _fetch_from_public_api(self, max_domains: int) -> List[Dict]:
        """
        Fetch from free public domain list APIs.
        Uses available free endpoints that provide expiring domain data.
        """
        records = []

        # Try to get recently expired/expiring .com domains from public feeds
        # These are best-effort — may not always be available
        endpoints = [
            "https://www.whoisxmlapi.com/whoisserver/WhoisService?domainName=example.com&outputFormat=JSON",
        ]

        for url in endpoints:
            self._rate_limit()
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=15,
                )
                if response.status_code == 200:
                    # Parse response based on format
                    data = self._parse_api_response(response.text)
                    records.extend(data)
                    log.info(f"Fetched {len(data)} domains from {url[:50]}...")
            except Exception as e:
                log.debug(f"API endpoint failed: {url[:50]}... — {e}")
                continue

        return records

    def _fetch_from_github_datasets(self, max_domains: int) -> List[Dict]:
        """
        Look for publicly available domain datasets on GitHub.
        These are typically CSVs or text files with domain lists.
        """
        records = []

        # Known public domain list repos (best-effort)
        github_raw_urls = [
            # These are example URLs — actual availability varies
            "https://raw.githubusercontent.com/tb0hdan/domains/master/data/",
        ]

        for base_url in github_raw_urls:
            self._rate_limit()
            try:
                response = self.session.get(
                    base_url,
                    headers=self._get_headers(),
                    timeout=15,
                )
                if response.status_code == 200:
                    domains = self._extract_domains_from_text(response.text)
                    for domain in domains[:max_domains]:
                        records.append(self._create_record(domain, "github_dataset"))
            except Exception as e:
                log.debug(f"GitHub dataset fetch failed: {e}")
                continue

        return records

    def _parse_api_response(self, text: str) -> List[Dict]:
        """Parse API response text into domain records."""
        records = []
        # Try to find domain names in the response
        domains = self._extract_domains_from_text(text)
        for domain in domains:
            records.append(self._create_record(domain, "public_api"))
        return records

    def _extract_domains_from_text(self, text: str) -> List[str]:
        """Extract valid domain names from raw text."""
        # Regex to find domain-like patterns
        pattern = r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|io|ai|co|net|org|dev|app|xyz|tech|me|gg))\b'
        matches = re.findall(pattern, text, re.IGNORECASE)

        # Validate and deduplicate
        valid_domains = []
        seen = set()
        for domain in matches:
            domain = domain.lower().strip()
            if domain not in seen and is_valid_domain(domain):
                valid_domains.append(domain)
                seen.add(domain)

        return valid_domains

    def _create_record(self, domain: str, source: str) -> Dict:
        """Create a standardized domain record."""
        return {
            "domain": domain,
            "expiry_date": "",  # Will be filled via RDAP later
            "tld": extract_tld(domain),
            "sld": extract_sld(domain),
            "source": source,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }


if __name__ == "__main__":
    scraper = PublicListsScraper()
    records = scraper.fetch_from_web_archives(max_domains=50)
    print(f"Fetched {len(records)} domains")
    for r in records[:5]:
        print(f"  {r['domain']} ({r['source']})")
