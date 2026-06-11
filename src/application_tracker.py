import json, sys
from pathlib import Path
from datetime import date
from config_loader import get_project_root

sys.stdout.reconfigure(encoding='utf-8')

TRACKER_PATH = get_project_root() / "output" / "applications_tracker.json"
VALID_STATUSES = {"pending", "sent", "replied", "interview", "offer", "rejected"}

def load() -> list:
    if TRACKER_PATH.exists():
        with open(TRACKER_PATH, encoding='utf-8') as f:
            return json.load(f)
    return []

def save(records: list):
    TRACKER_PATH.parent.mkdir(exist_ok=True)
    with open(TRACKER_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def add_application(company: str, role: str, email: str,
                     status: str = "pending", notes: str = "") -> dict:
    assert status in VALID_STATUSES, f"status must be one of {VALID_STATUSES}"
    records = load()
    record = {
        "company": company,
        "role": role,
        "email": email,
        "sent_date": str(date.today()),
        "status": status,
        "notes": notes,
    }
    records.append(record)
    save(records)
    print(f"  + Added: {company} — {role} ({status})")
    return record

def update_status(company: str, role: str, new_status: str, notes: str = ""):
    assert new_status in VALID_STATUSES
    records = load()
    for r in records:
        if r["company"] == company and r["role"] == role:
            r["status"] = new_status
            if notes:
                r["notes"] = notes
            save(records)
            print(f"  ✓ Updated: {company} — {role} → {new_status}")
            return r
    print(f"  ✗ Not found: {company} — {role}")
    return None

def print_summary():
    records = load()
    if not records:
        print("No applications tracked yet.")
        return
    from collections import Counter
    counts = Counter(r["status"] for r in records)
    print(f"\n=== Application Tracker ({len(records)} total) ===")
    for s in ["pending", "sent", "replied", "interview", "offer", "rejected"]:
        if counts.get(s):
            print(f"  {s:10s}: {counts[s]}")
    print()
    for r in records:
        print(f"  [{r['status']:10s}] {r['company'][:30]:30s} | {r['role'][:30]:30s} | {r['sent_date']}")

def seed_top5():
    """Pre-load the 5 priority jobs as 'pending'."""
    TOP5 = [
        ("امجاد العطاء", "IT Technician", "recruiterment.saudii@gmail.com"),
        ("ابراهيم بن سعيد للاستثمار", "Networking Pre-Sales Specialist", "recruiter.rawda.m@gmail.com"),
        ("شركة الخليج للكمبيوتر والمعدات الإلكترونية", "Network Technician", "hassankhaleej@gmail.com"),
        ("شركة القائد للإستثمار", "مهندس تطوير وبحث شبكات", "hr@leadergroup.com"),
        ("Al Ameri Engineering Consultants", "مهندس تقنية معلومات", "mohamedelammry@outlook.com"),
    ]
    for company, role, email in TOP5:
        add_application(company, role, email, status="pending")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'seed':
        seed_top5()
    elif len(sys.argv) > 1 and sys.argv[1] == 'update':
        # Usage: python application_tracker.py update "Company" "Role" "sent"
        if len(sys.argv) >= 5:
            update_status(sys.argv[2], sys.argv[3], sys.argv[4],
                          notes=sys.argv[5] if len(sys.argv) > 5 else "")
        else:
            print("Usage: application_tracker.py update <company> <role> <status> [notes]")
    else:
        print_summary()
