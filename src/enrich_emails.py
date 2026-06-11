"""
Hunter.io email enrichment — finds recruiter emails for job postings that have none.

Usage:
  PYTHONPATH=src python src/enrich_emails.py            # dry run
  PYTHONPATH=src python src/enrich_emails.py --write    # write enriched jobs JSON

Requires hunterio_api_key in config.json (free tier: 25 domain searches/month).
Get a key at https://hunter.io/users/sign_up
"""
import json, re, sys, argparse
import requests
from pathlib import Path
from config_loader import get_project_root, load_config

ROOT = get_project_root()
HUNTER_DOMAIN_URL = "https://api.hunter.io/v2/domain-search"


def company_to_domain(company_name: str) -> str:
    """Best-effort slug: 'Acme Corp Ltd' → 'acmecorp.com'."""
    slug = re.sub(r"[^\w]", "", company_name.lower())
    slug = re.sub(r"(ltd|llc|inc|corp|co|sa|group|holding|company)$", "", slug)
    return f"{slug}.com"


def find_domain_emails(domain: str, api_key: str, limit: int = 5) -> list:
    """Return list of email strings for a domain via Hunter.io Domain Search."""
    try:
        resp = requests.get(
            HUNTER_DOMAIN_URL,
            params={"domain": domain, "api_key": api_key, "limit": limit},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json().get("data", {})
        return [e["value"] for e in data.get("emails", []) if e.get("value")]
    except Exception:
        return []


def enrich_jobs(jobs: list, api_key: str, domain_map: dict = None) -> list:
    """Add Hunter.io emails to jobs that have none. No-op if api_key is empty."""
    if not api_key:
        return jobs
    domain_map = domain_map or {}
    enriched = []
    for job in jobs:
        if job.get("emails"):
            enriched.append(job)
            continue
        company = job.get("company", "")
        domain = domain_map.get(company) or company_to_domain(company)
        found = find_domain_emails(domain, api_key)
        job = dict(job)
        if found:
            job["emails"] = found
            job["email_source"] = "hunterio"
        enriched.append(job)
    return enriched


def main():
    p = argparse.ArgumentParser(description="Enrich job postings with Hunter.io emails")
    p.add_argument("--write", action="store_true", help="Write enriched JSON back to file")
    p.add_argument("--jobs", default=str(ROOT / "output" / "priority_jobs_matched.json"))
    args = p.parse_args()

    config = load_config()
    api_key = config.get("hunterio_api_key", "")

    if not api_key:
        print("No hunterio_api_key in config.json.")
        print("Add one (free at hunter.io) to use this feature.")
        sys.exit(0)

    with open(args.jobs, encoding="utf-8") as f:
        jobs = json.load(f)

    no_email = [j for j in jobs if not j.get("emails")]
    print(f"Jobs without email: {len(no_email)} / {len(jobs)}")

    enriched = enrich_jobs(jobs, api_key)
    gained = sum(1 for j in enriched if j.get("email_source") == "hunterio")
    print(f"Enriched: +{gained} emails found via Hunter.io")

    if args.write:
        with open(args.jobs, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)
        print(f"Written to {args.jobs}")
    else:
        print("Dry run — pass --write to save.")


if __name__ == "__main__":
    main()
