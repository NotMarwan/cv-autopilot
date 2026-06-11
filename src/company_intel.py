import json, re, sys
from collections import defaultdict
from pathlib import Path
from config_loader import get_project_root
ROOT = get_project_root()

sys.stdout.reconfigure(encoding='utf-8')

SECTOR_KEYWORDS = {
    'IT/Networking': ['network', 'cisco', 'ccnp', 'ccna', 'switch', 'router', 'lan', 'wan', 'infrastructure', 'شبكات', 'شبكة', 'شبكه'],
    'Cybersecurity': ['security', 'firewall', 'siem', 'pentest', 'vulnerability', 'حماية', 'أمن', 'امن', 'مراقبة', 'crowd control'],
    'IT Support/Sysadmin': ['it support', 'helpdesk', 'active directory', 'windows server', 'دعم تقني', 'exchange', 'it technician', 'it specialist'],
    'Project Management': ['project manager', 'pmp', 'pmo', 'مدير مشاريع', 'إدارة مشاريع', 'project plan', 'مشرف مشاريع'],
    'Telecom': ['telecom', 'telecommunication', 'اتصالات', 'gsm', 'fiber', '5g', 'rf', 'ivr', 'call center'],
    'Software Engineering': ['software', 'java', 'python', 'developer', 'backend', 'frontend', 'مطور', 'برمجة', 'software engineer'],
    'Sales/Pre-Sales': ['sales', 'pre-sales', 'مبيعات', 'account manager', 'business development', 'تنفيذي مبيعات'],
    'Banking/Finance': ['banking', 'finance', 'credit', 'relationship manager', 'sama', 'ifrs', 'بنك', 'مالية', 'استثمار'],
    'Engineering/Consulting': ['engineer', 'consulting', 'مهندس', 'استشارات', 'مشرف', 'mechanical', 'civil', 'electrical'],
    'Security/Guard': ['حارس أمن', 'security guard', 'crowd control', 'حراسة', 'حارس'],
}

TECH_TERMS = [
    'CCNP', 'CCNA', 'PMP', 'ITIL', 'AWS', 'Azure', 'Linux', 'Windows Server',
    'Active Directory', 'Exchange', 'Cisco', 'Fortinet', 'Palo Alto', 'Firewall',
    'SIEM', 'SOC', 'VMware', 'Python', 'Java', 'SQL', 'Power BI', 'Tableau',
    'Network+', 'Security+', 'CEH', 'CISSP', 'ISO 27001', 'Prince2',
    'Juniper', 'Aruba', 'F5', 'BGP', 'OSPF', 'MPLS', 'VPN', 'SD-WAN',
    'Docker', 'Kubernetes', 'DevOps', 'Git', 'Jira', 'Agile', 'Scrum',
    'SAP', 'Oracle', 'ERP', 'CRM', 'Salesforce', 'ServiceNow',
    'SAMA', 'IFRS', 'Basel', 'CFA', 'CPA', 'Bloomberg',
    'IVR', 'Genesys', 'Avaya', 'VOIP', 'SIP',
]

def classify_sector(title, description, requirements):
    text = f"{title} {description} {requirements}".lower()
    scores = {}
    for sector, kws in SECTOR_KEYWORDS.items():
        score = sum(1 for kw in kws if kw.lower() in text)
        if score > 0:
            scores[sector] = score
    if scores:
        return max(scores, key=scores.get)
    return 'General'

def extract_keywords(text):
    found = [t for t in TECH_TERMS if t.lower() in text.lower()]
    exp_match = re.findall(r'(\d+)\s*(?:to|-|–)\s*(\d+)\s*year', text, re.I)
    if exp_match:
        found.append(f"{exp_match[0][0]}-{exp_match[0][1]} yrs exp")
    elif re.search(r'(\d+)\s*years?\s+(?:of\s+)?experience', text, re.I):
        m = re.search(r'(\d+)\s*years?\s+(?:of\s+)?experience', text, re.I)
        found.append(f"{m.group(1)}+ yrs exp")
    return found

def run():
    with open(ROOT / "scratch" / "scraped_wadhefa_jobs.json", encoding='utf-8') as f:
        jobs = json.load(f)

    intel = {}
    sector_groups = defaultdict(list)

    for j in jobs:
        company = j.get('company', '').strip() or 'Unknown'
        title = j.get('title', '')
        desc = j.get('description', '') or ''
        reqs = j.get('requirements', '') or ''
        status = j.get('status', '')
        emails = j.get('emails', [])
        location = j.get('location', '')
        url = j.get('url', '')

        sector = classify_sector(title, desc, reqs)
        keywords = extract_keywords(f"{title} {desc} {reqs}")

        entry = {
            'company': company,
            'title': title,
            'sector': sector,
            'location': location,
            'status': status,
            'emails': emails,
            'keywords': keywords,
            'description': (desc or '')[:400],
            'requirements': (reqs or '')[:400],
            'url': url,
            'priority': 'HIGH' if status == 'Open' else ('MEDIUM' if emails else 'LOW'),
        }

        key = f"{company}|||{title}"
        intel[key] = entry
        sector_groups[sector].append(entry)

    with open(ROOT / "output" / "company_intel.json", 'w', encoding='utf-8') as f:
        json.dump(intel, f, ensure_ascii=False, indent=2)

    priority_order = ['HIGH', 'MEDIUM', 'LOW']
    lines = [
        '# Company Intelligence Map\n',
        f'**Total Jobs:** {len(jobs)} | **Sectors:** {len(sector_groups)} | **Open:** {sum(1 for j in jobs if j.get("status")=="Open")} | **Has Email:** {sum(1 for j in jobs if j.get("emails"))}\n',
        '',
    ]

    for sector in sorted(sector_groups.keys()):
        entries = sector_groups[sector]
        entries.sort(key=lambda x: priority_order.index(x['priority']) if x['priority'] in priority_order else 3)
        lines.append(f'\n## {sector} ({len(entries)} jobs)\n')
        for e in entries:
            badge = '🟢 OPEN' if e['priority'] == 'HIGH' else ('📧 EMAIL' if e['priority'] == 'MEDIUM' else '⛔ Closed')
            kw_str = ', '.join(e['keywords']) if e['keywords'] else '—'
            lines.append(f"### {badge} — {e['title']} @ {e['company']}")
            lines.append(f"- **Location:** {e['location']}")
            if e['emails']:
                lines.append(f"- **Email:** {', '.join(e['emails'])}")
            if e['url']:
                lines.append(f"- **URL:** {e['url']}")
            lines.append(f"- **Keywords:** {kw_str}")
            if e['requirements']:
                lines.append(f"- **Requirements:** {e['requirements'][:250]}")
            lines.append('')

    with open(ROOT / "output" / "company_map.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Done. {len(intel)} entries written.")
    sector_summary = {k: len(v) for k, v in sorted(sector_groups.items())}
    print(f"Sectors: {sector_summary}")
    return sector_groups

if __name__ == '__main__':
    run()
