"""
Web Alert Generator for the Domain Intelligence App.
Generates "Top Opportunities" data for the dashboard instead of Slack.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from utils.config import DATA_FILE, DATA_DIR
from utils.logger import get_logger

log = get_logger(__name__)

ALERTS_FILE = DATA_DIR / "top_opportunities.json"


def generate_top_opportunities(count: int = 10) -> List[Dict]:
    """
    Extract top N highest-scored domains for the dashboard alert section.
    
    Args:
        count: Number of top domains to extract.
    
    Returns:
        List of top domain dicts.
    """
    if not DATA_FILE.exists():
        log.warning("No data file found for alerts.")
        return []
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            domains = list(reader)
    except Exception as e:
        log.error(f"Failed to read data for alerts: {e}")
        return []
    
    # Sort by score descending
    domains.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    
    # Take top N
    top = domains[:count]
    
    # Save as JSON for dashboard
    alert_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(top),
        "domains": top,
    }
    
    try:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(alert_data, f, indent=2)
        log.info(f"Top {len(top)} opportunities saved to {ALERTS_FILE}")
    except Exception as e:
        log.error(f"Failed to save alerts: {e}")
    
    return top


def get_daily_summary(domains: List[Dict] = None) -> Dict:
    """Generate a summary dict for dashboard display."""
    if domains is None:
        if not DATA_FILE.exists():
            return {"total": 0, "high_value": 0, "expiring_24h": 0, "avg_score": 0}
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            domains = list(csv.DictReader(f))
    
    total = len(domains)
    high_value = sum(1 for d in domains if d.get("tag") == "High Value")
    expiring_24h = sum(1 for d in domains if str(d.get("expiry_window")) == "1 Day")
    scores = [float(d.get("score", 0)) for d in domains if d.get("score")]
    avg_score = round(sum(scores) / max(len(scores), 1), 1)
    
    return {
        "total": total,
        "high_value": high_value,
        "expiring_24h": expiring_24h,
        "avg_score": avg_score,
    }


if __name__ == "__main__":
    top = generate_top_opportunities()
    for d in top:
        print(f"  {d['domain']:30s} score={d.get('score', 'N/A'):>6s} tag={d.get('tag', 'N/A')}")
