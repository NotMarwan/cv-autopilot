import json, re, sys
from pathlib import Path
from config_loader import get_project_root
ROOT = get_project_root()

sys.stdout.reconfigure(encoding='utf-8')

KEYWORD_TAXONOMY = {
    'networking': ['CCNP', 'CCNA', 'BGP', 'OSPF', 'MPLS', 'SD-WAN', 'VPN', 'Cisco', 'Juniper', 'Aruba',
                   'switching', 'routing', 'LAN', 'WAN', 'firewall', 'Palo Alto', 'Fortinet', 'F5'],
    'security': ['CISSP', 'CEH', 'CISM', 'SOC', 'SIEM', 'penetration testing', 'vulnerability',
                 'ISO 27001', 'Security+', 'IDS', 'IPS', 'zero trust'],
    'cloud': ['AWS', 'Azure', 'GCP', 'DevOps', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'cloud'],
    'sysadmin': ['Active Directory', 'Windows Server', 'Exchange', 'VMware', 'Linux', 'ITIL',
                 'ServiceNow', 'Hyper-V', 'backup', 'DHCP', 'DNS'],
    'pm': ['PMP', 'Agile', 'Scrum', 'Prince2', 'Jira', 'MS Project', 'risk management',
           'stakeholder', 'budget', 'PMO', 'WBS', 'Gantt'],
    'banking': ['SAMA', 'IFRS', 'Basel III', 'CFA', 'credit analysis', 'relationship management',
                'AML', 'KYC', 'Bloomberg', 'trade finance', 'treasury', 'credit risk', 'portfolio'],
    'software': ['Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'REST API', 'Git',
                 'object-oriented', 'microservices', 'API'],
    'telecom': ['IVR', 'Genesys', 'Avaya', 'VOIP', 'SIP', 'contact center', 'call center',
                'GSM', 'fiber', '5G', 'RF', 'telecom'],
    'certifications': ['CCNP', 'CCNA', 'PMP', 'CISSP', 'CEH', 'AWS', 'Azure', 'ITIL', 'CFA',
                       'CPA', 'Security+', 'Network+', 'Prince2', 'CISM', 'ISO 27001'],
    'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
                    'bilingual', 'Arabic', 'English', 'presentation', 'negotiation'],
}

def extract_jd_keywords(title, description, requirements):
    text = f"{title} {description} {requirements}".lower()
    found = {}
    for category, terms in KEYWORD_TAXONOMY.items():
        matched = [t for t in terms if t.lower() in text]
        if matched:
            found[category] = matched
    exp = re.findall(r'(\d+)\s*(?:to|–|-)\s*(\d+)\s*year', text, re.I)
    if exp:
        found['experience_required'] = f"{exp[0][0]}-{exp[0][1]} years"
    else:
        m = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', text, re.I)
        if m:
            found['experience_required'] = f"{m.group(1)}+ years"
    # Check for bachelor's degree requirement
    if re.search(r'bachelor|bsc|بكالوريوس', text, re.I):
        found['education_required'] = "Bachelor's Degree"
    return found

def match_cv_to_job(cv, job_keywords):
    cv_text = json.dumps(cv, ensure_ascii=False).lower()
    matched = {}
    missing = {}
    for category, terms in job_keywords.items():
        if category in ('experience_required', 'education_required'):
            continue
        if isinstance(terms, list):
            hits = [t for t in terms if t.lower() in cv_text]
            gaps = [t for t in terms if t.lower() not in cv_text]
            if hits:
                matched[category] = hits
            if gaps:
                missing[category] = gaps

    total_jd = sum(len(v) for v in job_keywords.values() if isinstance(v, list))
    total_hit = sum(len(v) for v in matched.values())
    score = round((total_hit / max(total_jd, 1)) * 100)
    return {'matched': matched, 'missing': missing, 'score': score}

def generate_match_report():
    with open(ROOT / "scratch" / "scraped_wadhefa_jobs.json", encoding='utf-8') as f:
        jobs = json.load(f)
    with open(ROOT / "output" / "base_cv.json", encoding='utf-8') as f:
        cv = json.load(f)

    priority_jobs = [j for j in jobs if j.get('status') == 'Open' or j.get('emails')]
    lines = [
        '# CV-Job Match Report\n',
        f'**Base CV:** {cv.get("name", "User")} | **Priority jobs analyzed:** {len(priority_jobs)}\n',
        '',
    ]
    results = []

    for j in priority_jobs:
        title = j.get('title', '')
        company = (j.get('company') or 'Unknown')
        desc = j.get('description', '') or ''
        reqs = j.get('requirements', '') or ''
        jd_kws = extract_jd_keywords(title, desc, reqs)
        match = match_cv_to_job(cv, jd_kws)

        from company_intel import classify_sector
        sector = classify_sector(title, desc, reqs)

        results.append({**j, 'jd_keywords': jd_kws, 'match': match, 'sector': sector})

        badge = '🟢 OPEN' if j.get('status') == 'Open' else '📧 EMAIL'
        lines.append(f"## {badge} — {title} @ {company}")
        lines.append(f"- **Match Score:** {match['score']}%")
        if match['matched']:
            lines.append(f"- **✅ Matched:** {json.dumps(match['matched'], ensure_ascii=False)}")
        if match['missing']:
            lines.append(f"- **❌ Missing:** {json.dumps(match['missing'], ensure_ascii=False)}")
        if j.get('emails'):
            lines.append(f"- **📧 Apply to:** {', '.join(j['emails'])}")
        if j.get('url'):
            lines.append(f"- **URL:** {j['url']}")
        exp_req = jd_kws.get('experience_required', '')
        edu_req = jd_kws.get('education_required', '')
        if exp_req:
            lines.append(f"- **Experience Required:** {exp_req}")
        if edu_req:
            lines.append(f"- **Education Required:** {edu_req}")
        lines.append('')

    with open(ROOT / "output" / "match_report.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    with open(ROOT / "output" / "priority_jobs_matched.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Match report → output/match_report.md")
    print(f"Analyzed {len(results)} priority jobs")
    scores = sorted([r['match']['score'] for r in results], reverse=True)
    if scores:
        print(f"Scores: max={scores[0]}%, min={scores[-1]}%, avg={round(sum(scores)/len(scores))}%")
    return results

if __name__ == '__main__':
    generate_match_report()
