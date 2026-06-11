import json, os, re, sys, copy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def llm_rewrite_summary(title: str, company: str, sector: str,
                         base_summary: str, jd_keywords: dict) -> str:
    """Call Claude API to rewrite the CV summary for this specific job.
    Returns None silently if API key not set or call fails — caller falls back."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        kw_list = ", ".join(
            kw for cat_kws in jd_keywords.values()
            if isinstance(cat_kws, list) for kw in cat_kws
        )[:200]
        prompt = (
            f"Write a 3-sentence professional CV summary for a Computer Engineering graduate "
            f"applying for '{title}' at {company} (sector: {sector}). "
            f"Key job requirements: {kw_list}. "
            f"Candidate profile: {base_summary[:300]} "
            f"Rules: (1) Start with candidate background, not 'I'. "
            f"(2) Mention 2-3 specific job requirements naturally. "
            f"(3) End with motivation to join {company}. "
            f"Output ONLY the summary text, no labels."
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception:
        return None

SECTOR_RELEVANCE = {
    'IT/Networking': ['network', 'cisco', 'infrastructure', 'wan', 'lan', 'switch', 'router', 'deploy', 'maintain'],
    'Cybersecurity': ['security', 'firewall', 'compliance', 'risk', 'audit', 'protect', 'monitor'],
    'Project Management': ['project', 'deliver', 'stakeholder', 'plan', 'budget', 'team', 'manage', 'coordinate'],
    'Banking/Finance': ['portfolio', 'credit', 'risk', 'banking', 'client', 'revenue', 'compliance', 'finance', 'relation'],
    'IT Support/Sysadmin': ['support', 'server', 'user', 'deploy', 'maintain', 'incident', 'troubleshoot', 'install'],
    'Sales/Pre-Sales': ['sales', 'client', 'revenue', 'proposal', 'customer', 'target', 'account', 'business'],
    'Software Engineering': ['develop', 'code', 'implement', 'architect', 'api', 'database', 'test', 'deploy'],
    'Telecom': ['telecom', 'network', 'call', 'communication', 'ivr', 'voip', 'infrastructure'],
    'Engineering/Consulting': ['engineer', 'design', 'implement', 'consult', 'manage', 'supervise', 'quality'],
}

def tailor_summary(base_summary, company, title, jd_keywords, missing_kws):
    title = translate_title(title)
    all_matched = [kw for cat, kws in jd_keywords.items()
                   if isinstance(kws, list) for kw in kws]
    all_missing = [kw for kws in missing_kws.values() for kw in kws]

    # Paragraph 1: candidate background + target role (from the parsed base CV)
    para1 = base_summary if base_summary else (
        "Motivated graduate with a strong academic foundation and hands-on project experience."
    )

    # Paragraph 2: role alignment — matched keywords (no Arabic company name in LaTeX)
    if all_matched:
        kw_str = ', '.join(all_matched[:4])
        para2 = (
            f"Targeting the {title} role, with demonstrated skills in "
            f"{kw_str} that directly align with the position requirements."
        )
    else:
        para2 = (
            f"Eager to apply technical skills and academic foundation to the {title} role."
        )

    # Paragraph 3: growth / gaps (only if meaningful gaps exist)
    if all_missing and len(all_missing) <= 4:
        missing_str = ' and '.join(all_missing[:2])
        para3 = f"Actively developing proficiency in {missing_str} to fully meet the role requirements."
    else:
        para3 = ""

    parts = [para1, para2]
    if para3:
        parts.append(para3)
    return ' '.join(parts)

ARABIC_TITLES = {
    'مهندس تقنية معلومات':           'IT Engineer',
    'مهندس شبكات':                    'Network Engineer',
    'مهندس تطوير وبحث شبكات':        'Network R&D Engineer',
    'مهندس مشاريع':                   'Project Engineer',
    'مهندس بنية تحتية تقنية اول':     'Senior IT Infrastructure Engineer',
    'مهندس بنية تحتية تقنية':         'IT Infrastructure Engineer',
    'مشرف تقنية معلومات':             'IT Supervisor',
    'حارس أمن':                       'Security Guard',
    'حاسب كميات':                     'Quantity Surveyor',
    'اخصائي مبيعات حلول تقنية':       'IT Solutions Sales Specialist',
    'تنفيذي مبيعات تقنية':            'IT Sales Executive',
    'مدير اتصالات':                   'Telecom Manager',
    'أخصائي مبيعات':                  'Sales Specialist',
    'مهندس كهرباء':                   'Electrical Engineer',
    'مهندس ميكانيكا':                 'Mechanical Engineer',
    'مدير مشروع':                     'Project Manager',
    'محاسب':                          'Accountant',
    'مدير تقنية معلومات':             'IT Manager',
}

def translate_title(title: str) -> str:
    """Translate Arabic job title to English. Falls back to original if not in dict."""
    cleaned = title.strip()
    if cleaned in ARABIC_TITLES:
        return ARABIC_TITLES[cleaned]
    # If still contains Arabic characters, mark as IT Role to avoid LaTeX breakage
    if any('؀' <= c <= 'ۿ' for c in cleaned):
        return 'IT Role'
    return cleaned


def resolve_location(job_location: str, config=None) -> str:
    """Return CV location header. Uses config locations when available."""
    if config:
        current = config["user"]["location_current"]
        target  = config["user"]["location_target"]
        current_city = current.split(",")[0].strip().lower()
        loc = job_location.lower()
        if current_city in loc:
            return current
        return target
    # Legacy fallback
    loc = job_location.lower()
    if any(k in loc for k in ['jazan', 'جازان', 'jizan']):
        return 'Jazan, Saudi Arabia'
    return 'Riyadh, Saudi Arabia'


def score_bullet(bullet, terms):
    b = bullet.lower()
    return sum(1 for t in terms if t.lower() in b)

def select_relevant_bullets(experience, sector):
    terms = SECTOR_RELEVANCE.get(sector, [])
    result = []
    for role in experience:
        bullets = role.get('bullets', [])
        if not bullets:
            result.append(role)
            continue
        scored = sorted([(score_bullet(b, terms), b) for b in bullets], reverse=True)
        top = [b for _, b in scored[:5]]
        result.append({**role, 'bullets': top if top else bullets[:5]})
    return result

def tailor_skills(base_skills, jd_keywords, missing_kws):
    matched_flat = list(dict.fromkeys(
        kw for cat, kws in jd_keywords.items() if isinstance(kws, list) for kw in kws
    ))
    # Remove duplicates with base skills (case-insensitive)
    base_lower = {s.lower() for s in base_skills}
    new_kws = [kw for kw in matched_flat if kw.lower() not in base_lower]
    ordered = new_kws + base_skills
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for s in ordered:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(s)
    return deduped[:16]

def flatten_skills(skills_field):
    """Accept either a flat list or the new nested dict format."""
    if isinstance(skills_field, list):
        return skills_field
    if isinstance(skills_field, dict):
        flat = []
        for v in skills_field.values():
            if isinstance(v, dict):
                flat.extend(v.get('items', []))
            elif isinstance(v, list):
                flat.extend(v)
        return flat
    return []

def flatten_experience(experience):
    """Normalise experience entries: map 'responsibilities' → 'bullets'."""
    result = []
    for role in experience:
        entry = dict(role)
        if 'bullets' not in entry and 'responsibilities' in entry:
            entry['bullets'] = entry.pop('responsibilities')
        result.append(entry)
    return result

def run_tailor(use_llm=False, config=None):
    from config_loader import get_project_root, load_config
    ROOT = get_project_root()
    cfg = config if config is not None else load_config()

    with open(ROOT / "output" / "priority_jobs_matched.json", encoding='utf-8') as f:
        jobs = json.load(f)
    with open(ROOT / "output" / "base_cv.json", encoding='utf-8') as f:
        base_cv = json.load(f)

    out_dir = ROOT / "output" / "tailored_cvs"
    out_dir.mkdir(exist_ok=True)

    tailored_list = []
    seen_names = {}  # track filename collisions

    for j in jobs:
        company = (j.get('company') or 'Unknown').strip()
        title = (j.get('title') or 'Role').strip()
        sector = j.get('sector', 'General')
        jd_kws = j.get('jd_keywords', {})
        match = j.get('match', {})
        missing = match.get('missing', {})
        score = match.get('score', 0)

        tailored = copy.deepcopy(base_cv)
        tailored['_meta'] = {
            'target_company': company,
            'target_title': title,
            'target_sector': sector,
            'match_score': score,
            'apply_emails': j.get('emails', []),
            'job_url': j.get('url', ''),
            'status': j.get('status', ''),
            'location': j.get('location', ''),
        }

        base_summary = base_cv.get('summary', '') or base_cv.get(
            'summary_for_cv', {}).get('honest_profile', '')
        base_skills_flat = flatten_skills(base_cv.get('skills', []))
        base_experience = flatten_experience(base_cv.get('experience', []))

        tailored['title'] = translate_title(title)
        job_location = j.get('location', '')
        tailored['personal']['location'] = resolve_location(job_location, cfg)
        if use_llm:
            llm_result = llm_rewrite_summary(title, company, sector, base_summary, jd_kws)
            tailored['summary'] = llm_result if llm_result else tailor_summary(
                base_summary, company, title, jd_kws, missing
            )
        else:
            tailored['summary'] = tailor_summary(
                base_summary, company, title, jd_kws, missing
            )
        tailored['skills'] = tailor_skills(base_skills_flat, jd_kws, missing)
        tailored['experience'] = select_relevant_bullets(base_experience, sector)

        # Safe filename — deduplicate collisions by appending counter
        safe = re.sub(r'[^\w\s-]', '', f"{company}_{title}").replace(' ', '_')
        safe = safe[:55]
        seen_names[safe] = seen_names.get(safe, 0) + 1
        if seen_names[safe] > 1:
            safe = f"{safe}_{seen_names[safe]}"
        out_path = out_dir / f"{safe}_tailored.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(tailored, f, ensure_ascii=False, indent=2)

        tailored_list.append({
            'file': str(out_path),
            'score': score,
            'company': company,
            'title': title,
            'sector': sector,
            'emails': j.get('emails', []),
            'status': j.get('status', ''),
        })
        badge = '🟢' if j.get('status') == 'Open' else '📧'
        print(f"{badge} {company[:35]:35s} | {title[:35]:35s} | score: {score}%")

    print(f"\nDone. {len(tailored_list)} tailored CVs written → output/tailored_cvs/")
    return tailored_list

if __name__ == '__main__':
    run_tailor()
