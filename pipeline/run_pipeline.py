"""
Pipeline Orchestrator for the Domain Intelligence App.
Runs: ingest → clean → score → classify → save.
"""

import csv
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import DATA_DIR, DATA_FILE, MAX_DOMAINS_PER_RUN, SEED_DOMAIN_COUNT
from utils.helpers import is_valid_domain, clean_domain_name
from utils.logger import get_logger
from ingestion.seed_data import generate_seed_data
from scoring.scorer import DomainScorer
from utils.website_checker import validate_availability

log = get_logger(__name__)

CSV_FIELDS = [
    "domain", "sld", "tld", "availability_status",
    "score", "tag", "estimated_price",
    "keyword_score", "trend_score", "tld_score", "brandability_score", "length_score",
    "pronounceability_score", "source", "fetched_at", "scored_at", "country"
]


def load_existing_data() -> List[Dict]:
    """Load existing scored data from CSV."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        log.warning(f"Failed to load existing data: {e}")
        return []


def ingest_domains() -> List[Dict]:
    """Run all ingestion sources and merge results."""
    log.info("═" * 60)
    log.info("PHASE 1: DATA INGESTION")
    log.info("═" * 60)
    
    all_records = []
    
    # Source 1: Seed data (always available)
    log.info("Ingesting seed data...")
    seed_records = generate_seed_data(count=SEED_DOMAIN_COUNT)
    all_records.extend(seed_records)
    log.info(f"  → Seed: {len(seed_records)} domains")
    
    # Source 2: RDAP (best-effort, rate-limited)
    try:
        from ingestion.rdap_fetcher import RDAPFetcher
        fetcher = RDAPFetcher()
        # Try a small batch of well-known domains to supplement
        sample_domains = [
            "google.com", "facebook.com", "amazon.com", "netflix.com",
            "twitter.com", "github.com", "microsoft.com", "apple.com",
        ]
        rdap_records = fetcher.fetch_batch(sample_domains, max_count=5)
        all_records.extend(rdap_records)
        log.info(f"  → RDAP: {len(rdap_records)} domains")
    except Exception as e:
        log.warning(f"  → RDAP ingestion failed: {e}")
    
    # Source 3: Public lists (best-effort)
    try:
        from ingestion.public_lists import PublicListsScraper
        scraper = PublicListsScraper()
        public_records = scraper.fetch_from_web_archives(max_domains=50)
        all_records.extend(public_records)
        log.info(f"  → Public lists: {len(public_records)} domains")
    except Exception as e:
        log.warning(f"  → Public lists ingestion failed: {e}")
    
    log.info(f"Total ingested: {len(all_records)} domains")
    return all_records


def clean_data(records: List[Dict]) -> List[Dict]:
    """Deduplicate, validate, and normalize domain records."""
    log.info("═" * 60)
    log.info("PHASE 2: DATA CLEANING")
    log.info("═" * 60)
    
    seen = set()
    cleaned = []
    skipped = {"invalid": 0, "duplicate": 0, "no_expiry": 0}
    
    for record in records:
        domain = clean_domain_name(record.get("domain", ""))
        
        # Validate domain
        if not is_valid_domain(domain):
            skipped["invalid"] += 1
            continue
        
        # Deduplicate
        if domain in seen:
            skipped["duplicate"] += 1
            continue
        seen.add(domain)
        
        # Normalize
        record["domain"] = domain
        record["tld"] = record.get("tld", "." + domain.split(".")[-1])
        record["sld"] = record.get("sld", domain.split(".")[0])
        
        # Expiry logic removed as part of suggestion pivot
        
        cleaned.append(record)
    
    # Cap at max
    cleaned = cleaned[:MAX_DOMAINS_PER_RUN]
    
    log.info(f"Cleaned: {len(cleaned)} domains kept")
    log.info(f"Skipped: {skipped}")
    return cleaned


def score_domains(records: List[Dict]) -> List[Dict]:
    """Run ML scoring on all domains."""
    log.info("═" * 60)
    log.info("PHASE 3: ML SCORING")
    log.info("═" * 60)
    
    scorer = DomainScorer(use_pytrends=False)  # Static mode for CI
    scored = []
    
    for record in records:
        domain = record["domain"]
        try:
            scores = scorer.score_domain(domain)
            # Merge scores into record
            record.update(scores)
            record["scored_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            scored.append(record)
        except Exception as e:
            log.warning(f"Scoring failed for {domain}: {e}")
            continue
    
    log.info(f"Scored: {len(scored)} domains")
    
    # Sort by score descending
    scored.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    return scored


def save_results(records: List[Dict]) -> Path:
    """Save scored dataset to CSV."""
    log.info("═" * 60)
    log.info("PHASE 4: SAVING RESULTS")
    log.info("═" * 60)
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    
    log.info(f"Saved {len(records)} domains to {DATA_FILE}")
    
    # Stats
    high = sum(1 for r in records if r.get("tag") == "High Value")
    med = sum(1 for r in records if r.get("tag") == "Medium Value")
    low = sum(1 for r in records if r.get("tag") == "Low Value")
    log.info(f"Distribution: High={high}, Medium={med}, Low={low}")
    
    return DATA_FILE


def run_pipeline():
    """Execute the full pipeline: ingest → clean → score → save."""
    start = time.time()
    
    log.info("🚀 Domain Intelligence Pipeline Starting...")
    log.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    log.info("=" * 60)
    
    try:
        # Phase 1: Ingest
        raw_records = ingest_domains()
        
        # Phase 2: Clean
        cleaned = clean_data(raw_records)
        
        # Phase 2.5: Availability Validation
        cleaned = validate_availability(cleaned)
        
        if not cleaned:
            log.warning("No domains to score after cleaning. Using cached data.")
            return
        
        # Phase 3: Score
        scored = score_domains(cleaned)
        
        # Phase 4: Save
        output = save_results(scored)
        
        elapsed = time.time() - start
        log.info("=" * 60)
        log.info(f"✅ Pipeline complete in {elapsed:.1f}s")
        log.info(f"   Output: {output}")
        log.info(f"   Domains: {len(scored)}")
        log.info("=" * 60)
        
    except Exception as e:
        log.error(f"❌ Pipeline failed: {e}")
        # Fallback: keep existing data
        if DATA_FILE.exists():
            log.info("Existing data preserved as fallback.")
        raise


if __name__ == "__main__":
    run_pipeline()
