from pathlib import Path
import sys, json
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from unittest.mock import patch
from enrich_emails import find_domain_emails, enrich_jobs

HUNTER_RESPONSE = {
    "data": {
        "emails": [
            {"value": "john.doe@acme.com", "type": "personal", "confidence": 90},
            {"value": "hr@acme.com", "type": "generic", "confidence": 70},
        ]
    }
}


def test_find_domain_emails_returns_list():
    with patch("enrich_emails.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = HUNTER_RESPONSE
        result = find_domain_emails("acme.com", "fake_api_key")
    assert "hr@acme.com" in result
    assert "john.doe@acme.com" in result


def test_find_domain_emails_empty_on_error():
    with patch("enrich_emails.requests.get") as mock_get:
        mock_get.return_value.status_code = 401
        mock_get.return_value.json.return_value = {"errors": [{"details": "Invalid key"}]}
        result = find_domain_emails("acme.com", "bad_key")
    assert result == []


def test_enrich_jobs_adds_emails():
    jobs = [{"company": "Acme Corp", "url": "https://acme.com/jobs/1", "emails": []}]
    with patch("enrich_emails.find_domain_emails", return_value=["hr@acme.com"]):
        enriched = enrich_jobs(jobs, "fake_key", domain_map={"Acme Corp": "acme.com"})
    assert "hr@acme.com" in enriched[0]["emails"]


def test_enrich_jobs_skips_if_already_has_email():
    jobs = [{"company": "Acme Corp", "url": "...", "emails": ["existing@acme.com"]}]
    with patch("enrich_emails.find_domain_emails") as mock_find:
        enriched = enrich_jobs(jobs, "fake_key", domain_map={"Acme Corp": "acme.com"})
    mock_find.assert_not_called()
    assert enriched[0]["emails"] == ["existing@acme.com"]


def test_no_api_key_returns_jobs_unchanged():
    jobs = [{"company": "Acme Corp", "emails": []}]
    enriched = enrich_jobs(jobs, api_key="")
    assert enriched == jobs
