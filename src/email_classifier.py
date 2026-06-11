import json, sys
from pathlib import Path
from config_loader import get_project_root

sys.stdout.reconfigure(encoding='utf-8')

BASE = get_project_root()

SECTOR_RULES = {
    "Cybersecurity": {
        "rank": 1,
        "keywords": [
            "security", "cyber", "siem", "soc", "firewall", "sophos", "kaspersky",
            "fortinet", "palo alto", "splunk", "penetration", "vulnerability",
            "أمن", "حماية", "مخاطر", "اختراق", "تشفير", "cissp", "ceh", "iso 27001",
            "infosec", "nessus", "ids", "ips", "zero trust", "dlp"
        ]
    },
    "IT/Networking": {
        "rank": 2,
        "keywords": [
            "network", "cisco", "switching", "routing", "wan", "lan", "infrastructure",
            "تقنية", "شبكات", "it ", "information technology", "نظم", "حاسب",
            "ccna", "ccnp", "juniper", "aruba", "mikrotik", "wireless", "wi-fi",
            "data center", "noc", "helpdesk", "support", "sysadmin", "server"
        ]
    },
    "Telecom": {
        "rank": 3,
        "keywords": [
            "telecom", "telecommunication", "اتصالات", "stc", "mobily", "zain",
            "fiber", "5g", "rf", "voip", "sip", "antenna", "bts", "nsa", "iptv"
        ]
    },
    "Software/Cloud": {
        "rank": 4,
        "keywords": [
            "software", "developer", "cloud", "aws", "azure", "devops", "docker",
            "kubernetes", "برمجة", "تطوير", "python", "java", "api", "saas"
        ]
    },
}

def classify_entry(entry: dict) -> dict:
    """Add priority_sector and priority_rank to an email entry. Never removes entries."""
    text = (
        (entry.get("company") or "") + " " +
        (entry.get("industry") or "") + " " +
        (entry.get("website") or "")
    ).lower()

    for sector, cfg in SECTOR_RULES.items():
        if any(kw in text for kw in cfg["keywords"]):
            return {**entry, "priority_sector": sector, "priority_rank": cfg["rank"]}

    return {**entry, "priority_sector": "Other", "priority_rank": 5}

def run_classify(input_path=None, output_path=None):
    inp = Path(input_path) if input_path else BASE / "jazan_emails_all.json"
    out = Path(output_path) if output_path else BASE / "output" / "email_classified.json"

    with open(inp, encoding='utf-8') as f:
        emails = json.load(f)

    classified = [classify_entry(e) for e in emails]
    classified.sort(key=lambda x: (x["priority_rank"], x.get("company", "")))

    out.parent.mkdir(exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    from collections import Counter
    counts = Counter(e["priority_sector"] for e in classified)
    print(f"\nClassified {len(classified)} emails:")
    for sector in ["Cybersecurity", "IT/Networking", "Telecom", "Software/Cloud", "Other"]:
        rank = SECTOR_RULES.get(sector, {}).get("rank", 5)
        print(f"  Rank {rank} — {sector:20s}: {counts.get(sector, 0)}")
    print(f"\nOutput: {out}")
    return classified

if __name__ == '__main__':
    run_classify()
