import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from email_classifier import classify_entry, SECTOR_RULES

def test_cybersecurity_priority():
    entry = {"company": "Saudi SIEM & SOC Solutions", "industry": "security", "email": "a@b.com"}
    result = classify_entry(entry)
    assert result["priority_sector"] == "Cybersecurity"
    assert result["priority_rank"] == 1

def test_networking_rank():
    entry = {"company": "Cisco Partner KSA", "industry": "networking", "email": "a@b.com"}
    result = classify_entry(entry)
    assert result["priority_sector"] == "IT/Networking"
    assert result["priority_rank"] == 2

def test_unknown_kept_as_other():
    entry = {"company": "Al Rajhi Bakery", "industry": "", "email": "a@b.com"}
    result = classify_entry(entry)
    assert result["priority_sector"] == "Other"
    assert result["priority_rank"] == 5
    assert "email" in result

def test_arabic_cybersecurity():
    entry = {"company": "شركة أمن المعلومات", "industry": "", "email": "a@b.com"}
    result = classify_entry(entry)
    assert result["priority_sector"] == "Cybersecurity"
