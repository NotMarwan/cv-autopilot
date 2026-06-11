import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def _get_config(config):
    """Return passed config or load default from config.json."""
    if config is not None:
        return config
    from config_loader import load_config
    return load_config()


def classify_role(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ['network', 'ccna', 'routing', 'switching', 'cisco', 'infrastructure', 'technician', 'noc']):
        return 'networking'
    if any(k in t for k in ['security', 'cyber', 'soc', 'pentest', 'firewall', 'threat']):
        return 'security'
    if any(k in t for k in ['software', 'developer', 'full', 'frontend', 'backend', 'web', 'saas']):
        return 'software'
    if any(k in t for k in ['data', 'analyst', 'ai', 'machine', 'ml', 'python']):
        return 'data'
    if any(k in t for k in ['pre-sales', 'sales', 'presales', 'business']):
        return 'sales'
    if any(k in t for k in ['it support', 'helpdesk', 'it technician', 'desktop', 'support']):
        return 'support'
    return 'general'


def pick_projects(category: str, config: dict) -> tuple:
    """Return (project_paragraphs, coop_sentence) for this role category."""
    projects = config.get("projects", {})
    role_map = config.get("role_project_map", {})
    keys = role_map.get(category, list(projects.keys())[:2])
    paras = [projects[k] for k in keys if k in projects and k != "coop"]
    coop = projects.get("coop", "")
    return "\n\n".join(paras), coop


def build_cover_email(title: str, company: str, to_email: str,
                      score: int = 0, config: dict = None) -> str:
    cfg = _get_config(config)
    user = cfg["user"]
    subject = f"Subject: Application for {title} — {user['name']}"
    category = classify_role(title)
    project_para, coop_para = pick_projects(category, cfg)

    ccna_line = ", CCNA certified" if user.get("ccna") else ""
    gpa_line = f" (GPA {user['gpa']}, class of {user.get('grad_year', '2026')})" if user.get("gpa") else ""

    body = f"""To the Hiring Team at {company},

I am writing to express my interest in the {title} position. I am a Computer Engineering and Networks graduate{gpa_line}{ccna_line}.

{project_para}

{coop_para}

I would welcome the opportunity to bring this combination of academic foundation, hands-on field experience, and independent project execution to {company}. Please find my tailored CV attached.

Best regards,
{user['name']}
{user['email']} | {user['phone']}
{user['linkedin']}"""

    return f"{subject}\nTo: {to_email}\n\n{body}"


def run_cover(jobs_path=None, output_dir=None, config=None):
    from config_loader import get_project_root
    ROOT = get_project_root()
    cfg = _get_config(config)

    jobs_path  = Path(jobs_path)  if jobs_path  else ROOT / "output" / "priority_jobs_matched.json"
    output_dir = Path(output_dir) if output_dir else ROOT / "output" / "cover_emails"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(jobs_path, encoding='utf-8') as f:
        jobs = json.load(f)

    email_jobs = [j for j in jobs if j.get('emails')]
    email_jobs.sort(key=lambda x: x.get('match', {}).get('score', 0), reverse=True)

    generated = []
    for j in email_jobs:
        company   = (j.get('company') or 'Unknown').strip()
        title     = (j.get('title')   or 'Role').strip()
        score     = j.get('match', {}).get('score', 0)
        to_emails = j.get('emails', [])

        for to_email in to_emails:
            body     = build_cover_email(title, company, to_email, score, config=cfg)
            safe     = re.sub(r'[^\w\s-]', '', f"{company}_{title}").replace(' ', '_')[:50]
            out_path = output_dir / f"{safe}_cover.txt"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(body)
            cat = classify_role(title)
            print(f"  {company[:30]:30s} | {title[:25]:25s} | {cat:10s} | {score}%")
            generated.append(str(out_path))

    print(f"\n{len(generated)} cover emails written to output/cover_emails/")
    return generated


if __name__ == '__main__':
    run_cover()
