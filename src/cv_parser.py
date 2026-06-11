"""
Converts the user's CV (LaTeX or plain text) into structured JSON.

Usage:
  python src/cv_parser.py                    # default: parse ATS_CV_SABB.tex
  python src/cv_parser.py --cv your_cv.tex   # your LaTeX CV
  python src/cv_parser.py --cv your_cv.txt   # plain text CV
"""
import json, sys, re, argparse
from pathlib import Path
from config_loader import get_project_root
_ROOT = get_project_root()

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_CV = str(_ROOT / "ATS_CV_SABB.tex")
OUTPUT_PATH = str(_ROOT / "output" / "base_cv.json")

def parse_tex(tex_text):
    cv = {
        'name': '',
        'title': '',
        'contact': {},
        'summary': '',
        'skills': [],
        'experience': [],
        'education': [],
        'certifications': [],
        'languages': [],
        'volunteering': [],
    }

    # Name — first \textbf{...} inside \begin{center}
    center_m = re.search(r'\\begin\{center\}(.*?)\\end\{center\}', tex_text, re.DOTALL)
    if center_m:
        center_block = center_m.group(1)
        name_m = re.search(r'\\textbf\{([^}]+)\}', center_block)
        if name_m:
            cv['name'] = name_m.group(1).strip()
        title_m = re.search(r'\\large\\textbf\{([^}]+)\}', center_block)
        if title_m:
            cv['title'] = title_m.group(1).strip().replace(' --', ' —')

    # Contact
    email_m = re.search(r'href\{mailto:([^}]+)\}', tex_text)
    phone_m = re.search(r'\+\d[\d\s]+', tex_text)
    linkedin_m = re.search(r'href\{(https?://linkedin[^}]+)\}', tex_text)
    if email_m:
        cv['contact']['email'] = email_m.group(1)
    if phone_m:
        cv['contact']['phone'] = phone_m.group(0).strip()
    if linkedin_m:
        cv['contact']['linkedin'] = linkedin_m.group(1)

    def section_body(name, tex):
        """Extract body between \\section{name} and next \\section{"""
        pattern = rf'\\section\{{{re.escape(name)}\}}(.*?)(?=\\section\{{|\Z)'
        m = re.search(pattern, tex, re.DOTALL)
        return m.group(1) if m else ''

    def clean(s):
        s = re.sub(r'\\(textbf|textit|large|small|LARGE|hfill|quad)\b', '', s)
        s = re.sub(r'\\[a-zA-Z]+\*?\s*\{[^}]*\}', '', s)
        s = re.sub(r'\\[a-zA-Z]+\*?', '', s)
        s = re.sub(r'[{}]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    # Summary
    summary_body = section_body('Professional Summary', tex_text)
    cv['summary'] = clean(summary_body)

    # Core Skills
    skills_body = section_body('Core Skills', tex_text)
    raw_skills = re.split(r'\\quad|\\\\|\n', skills_body)
    cv['skills'] = [clean(s) for s in raw_skills if len(clean(s)) > 2]

    # Professional Experience
    exp_body = section_body('Professional Experience', tex_text)
    subsections = re.split(r'\\subsection\*', exp_body)
    for sub in subsections[1:]:
        header_m = re.match(r'\{(.+?)\}', sub, re.DOTALL)
        company_m = re.search(r'\\textit\{([^}]+)\}', sub)
        bullets = re.findall(r'\\item\s+(.+?)(?=\\item|\\end\{itemize\}|\Z)', sub, re.DOTALL)
        if header_m:
            role_raw = header_m.group(1)
            # Split role and date on \hfill
            role_parts = re.split(r'\\hfill', role_raw)
            role = clean(role_parts[0])
            dates = clean(role_parts[1]) if len(role_parts) > 1 else ''
            company = clean(company_m.group(1)) if company_m else ''
            clean_bullets = [clean(b) for b in bullets if clean(b)]
            cv['experience'].append({
                'role': role,
                'company': company,
                'dates': dates,
                'bullets': clean_bullets,
            })

    # Education
    edu_body = section_body('Education', tex_text)
    edu_subsections = re.split(r'\\subsection\*', edu_body)
    for sub in edu_subsections[1:]:
        header_m = re.match(r'\{(.+?)\}', sub, re.DOTALL)
        school_m = re.search(r'\\textit\{([^}]+)\}', sub)
        if header_m:
            parts = re.split(r'\\hfill', header_m.group(1))
            degree = clean(parts[0])
            year = clean(parts[1]) if len(parts) > 1 else ''
            school = clean(school_m.group(1)) if school_m else ''
            bullets = re.findall(r'\\item\s+(.+?)(?=\\item|\\end\{itemize\}|\Z)', sub, re.DOTALL)
            cv['education'].append({
                'degree': degree,
                'school': school,
                'year': year,
                'details': [clean(b) for b in bullets if clean(b)],
            })

    # Certifications
    cert_body = section_body('Certifications', tex_text)
    certs = re.findall(r'\\item\s+(.+?)(?=\\item|\\end\{itemize\}|\Z)', cert_body, re.DOTALL)
    cv['certifications'] = [clean(c) for c in certs if clean(c)]

    # Technical Skills
    tech_body = section_body('Technical Skills', tex_text)
    tech_bullets = re.findall(r'\\item\s+(.+?)(?=\\item|\\end\{itemize\}|\Z)', tech_body, re.DOTALL)
    cv['technical_skills'] = [clean(t) for t in tech_bullets if clean(t)]

    # Languages
    lang_body = section_body('Languages', tex_text)
    cv['languages'] = [l.strip() for l in re.split(r'\\;?\|\\;?|\\quad', clean(lang_body)) if l.strip()]

    return cv

SECTION_ALIASES = {
    'summary':        ['summary', 'profile', 'objective', 'about', 'professional summary'],
    'skills':         ['skills', 'core skills', 'technical skills', 'key skills'],
    'experience':     ['experience', 'work experience', 'professional experience', 'employment'],
    'education':      ['education', 'academic background'],
    'certifications': ['certifications', 'certificates', 'licenses'],
    'languages':      ['languages'],
}

def _match_section(line):
    """Return the canonical section key if this line is a section header."""
    stripped = line.strip().rstrip(':')
    if not stripped or stripped != stripped.upper():
        return None
    low = stripped.lower()
    for key, aliases in SECTION_ALIASES.items():
        if low in aliases:
            return key
    return None

def parse_plaintext(text):
    """Parse a plain-text CV using ALL-CAPS section headers (SUMMARY, SKILLS, ...)."""
    cv = {
        'name': '', 'title': '', 'contact': {},
        'summary': '', 'skills': [], 'experience': [],
        'education': [], 'certifications': [], 'languages': [],
    }
    lines = [l.rstrip() for l in text.strip().split('\n')]
    nonempty = [l.strip() for l in lines if l.strip()]
    if nonempty:
        cv['name'] = nonempty[0]
    if len(nonempty) > 1 and '@' not in nonempty[1]:
        cv['title'] = nonempty[1]
    email_m = re.search(r'[\w.+-]+@[\w.]+\.\w+', text)
    if email_m:
        cv['contact']['email'] = email_m.group(0)
    phone_m = re.search(r'\+\d[\d\s\-]{8,}', text)
    if phone_m:
        cv['contact']['phone'] = phone_m.group(0).strip()

    # Bucket lines under ALL-CAPS section headers
    sections = {}
    current = None
    for line in lines:
        stripped = line.strip()
        sec = _match_section(stripped) if stripped else None
        if sec:
            current = sec
            sections[current] = []
        elif current and stripped:
            sections[current].append(stripped)

    if 'summary' in sections:
        cv['summary'] = ' '.join(sections['summary'])
    if 'skills' in sections:
        raw = ' '.join(sections['skills'])
        cv['skills'] = [s.strip() for s in re.split(r'[,;·|]', raw) if len(s.strip()) > 1]
    if 'experience' in sections:
        entries, role, bullets = [], None, []
        for line in sections['experience']:
            if line.startswith(('-', '*', '•')):
                bullets.append(line.lstrip('-*• ').strip())
            else:
                if role:
                    entries.append({'title': role, 'bullets': bullets})
                role, bullets = line, []
        if role:
            entries.append({'title': role, 'bullets': bullets})
        cv['experience'] = entries
    if 'education' in sections:
        cv['education'] = sections['education']
    if 'certifications' in sections:
        cv['certifications'] = sections['certifications']
    if 'languages' in sections:
        cv['languages'] = sections['languages']
    return cv

def run(cv_path=None):
    path = cv_path or DEFAULT_CV
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if path.endswith('.tex'):
        cv = parse_tex(content)
    else:
        cv = parse_plaintext(content)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(cv, f, ensure_ascii=False, indent=2)

    print(f"CV parsed → {OUTPUT_PATH}")
    print(f"Name      : {cv['name']}")
    print(f"Title     : {cv['title']}")
    print(f"Skills    : {len(cv.get('skills', []))}")
    print(f"Experience: {len(cv.get('experience', []))} roles")
    print(f"Education : {len(cv.get('education', []))} entries")
    print(f"Certs     : {len(cv.get('certifications', []))}")
    return cv

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--cv', default=None, help='Path to your CV (.tex or .txt)')
    args = p.parse_args()
    run(cv_path=args.cv)
