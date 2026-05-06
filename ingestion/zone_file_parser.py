"""
Zone File Parser for the Domain Intelligence App.

Parses domain data from publicly available zone file snippets
and DNS data sources. Extensible for ICANN CZDS integration.
"""

import re
from typing import List, Dict
from datetime import datetime, timezone

from utils.helpers import is_valid_domain, extract_tld, extract_sld
from utils.logger import get_logger

log = get_logger(__name__)


class ZoneFileParser:
    """
    Parses zone file data to extract domain names.
    
    Zone files contain DNS records for TLD zones. While full access
    requires ICANN CZDS approval, some data is publicly accessible.
    """

    def parse_zone_text(self, text: str, tld: str = ".com") -> List[Dict]:
        """
        Parse raw zone file text to extract domain names.
        
        Zone file format (simplified):
        domain.com.  IN  NS  ns1.example.com.
        domain.com.  IN  A   93.184.216.34
        
        Args:
            text: Raw zone file content.
            tld: The TLD this zone file represents.
        
        Returns:
            List of domain records.
        """
        records = []
        seen = set()

        lines = text.strip().split("\n")
        log.info(f"Parsing zone file: {len(lines)} lines")

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith(";") or line.startswith("$"):
                continue

            # Extract domain from zone file record
            domain = self._extract_domain_from_line(line, tld)
            if domain and domain not in seen:
                seen.add(domain)
                records.append({
                    "domain": domain,
                    "expiry_date": "",  # Zone files don't contain expiry data
                    "tld": extract_tld(domain),
                    "sld": extract_sld(domain),
                    "source": "zone_file",
                    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                })

        log.info(f"Extracted {len(records)} domains from zone file")
        return records

    def _extract_domain_from_line(self, line: str, tld: str) -> str:
        """
        Extract domain name from a zone file line.
        
        Args:
            line: Single line from zone file.
            tld: Expected TLD.
        
        Returns:
            Domain name or empty string if not parseable.
        """
        parts = line.split()
        if not parts:
            return ""

        # First field is typically the domain name
        candidate = parts[0].rstrip(".")

        # Validate
        if not candidate:
            return ""

        # Ensure it has the right TLD
        if not candidate.endswith(tld.lstrip(".")):
            # Try to append TLD if it's just the SLD
            if "." not in candidate:
                candidate = f"{candidate}{tld}"

        if is_valid_domain(candidate):
            return candidate.lower()

        return ""

    def parse_domain_list_file(self, filepath: str) -> List[Dict]:
        """
        Parse a simple text file containing one domain per line.
        
        Args:
            filepath: Path to the domain list file.
        
        Returns:
            List of domain records.
        """
        records = []
        seen = set()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    domain = line.strip().lower()
                    if domain and domain not in seen and is_valid_domain(domain):
                        seen.add(domain)
                        records.append({
                            "domain": domain,
                            "expiry_date": "",
                            "tld": extract_tld(domain),
                            "sld": extract_sld(domain),
                            "source": "domain_list",
                            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                        })
        except FileNotFoundError:
            log.warning(f"Domain list file not found: {filepath}")
        except Exception as e:
            log.error(f"Error parsing domain list: {e}")

        log.info(f"Parsed {len(records)} domains from list file")
        return records


if __name__ == "__main__":
    parser = ZoneFileParser()

    # Example zone file content
    sample = """
    ; Zone file sample
    example.com.    IN  NS  ns1.example.com.
    testsite.com.   IN  A   93.184.216.34
    myapp.com.      IN  NS  ns2.myapp.com.
    """

    records = parser.parse_zone_text(sample, tld=".com")
    for r in records:
        print(f"  {r['domain']} ({r['source']})")
