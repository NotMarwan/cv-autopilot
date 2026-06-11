from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from cover_email_generator import build_cover_email

SAMPLE_CONFIG = {
    "user": {
        "name": "Jane Doe", "email": "jane@example.com",
        "phone": "+1 555 000 0000", "linkedin": "linkedin.com/in/jane",
        "location_current": "Riyadh, Saudi Arabia",
        "location_target": "Riyadh, Saudi Arabia",
        "gpa": "3.9/4.0", "grad_year": "2025", "ccna": True,
    },
    "projects": {
        "project1": "Built X system. 99.9% uptime, 207 commits.",
        "coop": "8-week co-op at Acme Corp. Grade A+. Hands-on with Cisco gear.",
    },
    "role_project_map": {
        "networking": ["project1"],
        "general": ["project1"],
    },
}


def test_contains_job_title():
    email = build_cover_email("Network Engineer", "Cisco KSA", "hr@cisco.com", config=SAMPLE_CONFIG)
    assert "Network Engineer" in email


def test_contains_company():
    email = build_cover_email("IT Specialist", "Al Ameri", "hr@alameri.com", config=SAMPLE_CONFIG)
    assert "Al Ameri" in email


def test_contains_config_name():
    email = build_cover_email("IT Technician", "Amjad", "a@b.com", config=SAMPLE_CONFIG)
    assert "Jane Doe" in email


def test_contains_config_phone():
    email = build_cover_email("IT Technician", "Amjad", "a@b.com", config=SAMPLE_CONFIG)
    assert "+1 555 000 0000" in email


def test_has_subject_line():
    email = build_cover_email("Network Engineer", "STC", "hr@stc.com", config=SAMPLE_CONFIG)
    assert email.startswith("Subject:")


def test_no_hardcoded_personal_data():
    email = build_cover_email("Network Engineer", "STC", "hr@stc.com", config=SAMPLE_CONFIG)
    assert "Marwan" not in email
    assert "marwansalahmohammed" not in email
    assert "+966" not in email
