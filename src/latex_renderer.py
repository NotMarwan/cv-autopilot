"""
Renders tailored CV JSON files into LaTeX (.tex) and optionally PDF via xelatex.
"""
import json, subprocess, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def strip_arabic(s: str) -> str:
    """Remove Arabic characters — they render as broken text in LaTeX without arabxetex."""
    return ''.join(c for c in s if not ('؀' <= c <= 'ۿ' or 'ݐ' <= c <= 'ݿ'))

def escape_tex(s):
    if not s:
        return ''
    s = strip_arabic(str(s))
    for old, new in [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('^', r'\^{}'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('—', '--'),
        ('–', '--'),
    ]:
        s = s.replace(old, new)
    return s

def build_experience_section(experience):
    if not experience:
        return ''
    lines = [r'\section{Professional Experience}']
    for role in experience:
        role_title = escape_tex(role.get('title', role.get('role', '')))
        company = escape_tex(role.get('employer', role.get('company', '')))
        dates = escape_tex(role.get('duration', role.get('dates', '')))
        bullets = role.get('bullets', role.get('responsibilities', []))
        header = f'\\subsection*{{{role_title} \\hfill {dates}}}' if dates else f'\\subsection*{{{role_title}}}'
        lines.append(header)
        lines.append(f'\\textit{{{company}}}')
        if bullets:
            lines.append(r'\begin{itemize}')
            for b in bullets:
                clean_b = escape_tex(b)
                if clean_b:
                    lines.append(f'  \\item {clean_b}')
            lines.append(r'\end{itemize}')
    return '\n'.join(lines)

def build_education_section(education):
    if not education:
        return ''
    lines = [r'\section{Education}']
    for edu in education:
        degree = escape_tex(edu.get('degree', ''))
        school = escape_tex(edu.get('university', edu.get('school', '')))
        year = escape_tex(str(edu.get('expected_graduation', edu.get('year', ''))))
        gpa = edu.get('gpa', '')
        header = f'\\subsection*{{{degree} \\hfill {year}}}' if year else f'\\subsection*{{{degree}}}'
        lines.append(header)
        if school:
            lines.append(f'\\textit{{{school}}}')
        if gpa:
            lines.append(f'GPA: {escape_tex(gpa)}')
        details = edu.get('details', edu.get('relevant_courses', []))
        if details:
            lines.append(r'\begin{itemize}')
            for d in details[:6]:
                if escape_tex(d):
                    lines.append(f'  \\item {escape_tex(d)}')
            lines.append(r'\end{itemize}')
    return '\n'.join(lines)

def build_certs_section(certs):
    if not certs:
        return ''
    lines = [r'\section{Certifications}', r'\begin{itemize}']
    for c in certs:
        ec = escape_tex(c)
        if ec:
            lines.append(f'  \\item {ec}')
    lines.append(r'\end{itemize}')
    return '\n'.join(lines)

def build_tech_skills_section(tech_skills):
    if not tech_skills:
        return ''
    lines = [r'\section{Technical Skills}', r'\begin{itemize}']
    for t in tech_skills:
        et = escape_tex(t)
        if et:
            lines.append(f'  \\item {et}')
    lines.append(r'\end{itemize}')
    return '\n'.join(lines)

def build_projects_section(projects):
    if not projects:
        return ''
    lines = [r'\section{Projects}']
    for p in projects:
        title = escape_tex(p.get('title', ''))
        period = escape_tex(str(p.get('period', p.get('course', ''))))
        ptype = escape_tex(p.get('type', ''))
        header = f'\\subsection*{{{title} \\hfill {period}}}' if period else f'\\subsection*{{{title}}}'
        lines.append(header)
        if ptype:
            lines.append(f'\\textit{{{ptype}}}')
        achievements = p.get('key_achievements', p.get('my_contributions', []))
        metrics = p.get('metrics', {})
        if achievements:
            lines.append(r'\begin{itemize}')
            for a in achievements[:3]:
                ea = escape_tex(a)
                if ea:
                    lines.append(f'  \\item {ea}')
            lines.append(r'\end{itemize}')
        elif metrics:
            lines.append(r'\begin{itemize}')
            for k, v in list(metrics.items())[:3]:
                lines.append(f'  \\item {escape_tex(k)}: {escape_tex(str(v))}')
            lines.append(r'\end{itemize}')
    return '\n'.join(lines)

TEX_DOC = r"""\documentclass[10pt,a4paper]{{article}}
\usepackage[hmargin=2cm,vmargin=2cm]{{geometry}}
\usepackage{{fontspec}}
\setmainfont{{Arial}}
\usepackage{{setspace}}
\setstretch{{1.05}}
\usepackage[colorlinks=true,urlcolor=blue,pdfborder={{0 0 0}}]{{hyperref}}
\usepackage{{parskip}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{3pt}}
\usepackage{{titlesec}}
\pagestyle{{empty}}
\titleformat{{\section}}{{\large\bfseries}}{{}}{{0pt}}{{}}[\vspace{{-4pt}}\rule{{\textwidth}}{{0.6pt}}\vspace{{-6pt}}]
\titlespacing*{{\section}}{{0pt}}{{10pt}}{{4pt}}
\titleformat{{\subsection}}[runin]{{\bfseries}}{{}}{{0pt}}{{}}
\titlespacing*{{\subsection}}{{0pt}}{{4pt}}{{6pt}}

\begin{{document}}

\begin{{center}}
  {{\LARGE\textbf{{{name}}}}}\\[4pt]
  \large\textbf{{{title}}}\\[4pt]
  \small
  {location}
  \href{{mailto:{email_raw}}}{{{email_raw}}} \quad
  {phone_block}
  \href{{https://{linkedin_raw}}}{{{linkedin_raw}}}
\end{{center}}

\vspace{{-2pt}}

\section{{Professional Summary}}

{summary}

\section{{Core Skills}}

{skills_line}

{experience_section}

{projects_section}

{education_section}

{certs_section}

\section{{Languages}}

{languages_line}

\end{{document}}
"""

def render_cv(cv_json_path, compile_pdf=True):
    with open(cv_json_path, encoding='utf-8') as f:
        cv = json.load(f)

    meta = cv.get('_meta', {})
    # Support both old {contact:{}} and new {personal:{}} format
    personal = cv.get('personal', cv.get('contact', {}))

    email = personal.get('email', '')
    phone = personal.get('phone', '')
    linkedin = personal.get('linkedin', '')
    location = personal.get('location', meta.get('location', ''))

    email_raw    = email.replace('https://', '')
    linkedin_raw = linkedin.replace('https://', '').replace('http://', '')
    phone_block    = f'{escape_tex(phone)} \\quad' if phone else ''
    location_block = f'{escape_tex(location)} \\quad' if location else ''

    skills = cv.get('skills', [])
    skills_line = ' \\quad\n'.join(escape_tex(s) for s in skills if s and isinstance(s, str))

    # Normalise education: accept dict or list
    edu_raw = cv.get('education', [])
    if isinstance(edu_raw, dict):
        edu_list = [edu_raw]
    else:
        edu_list = edu_raw

    # Normalise certifications: accept list of dicts or list of strings
    certs_raw = cv.get('certifications', [])
    certs_flat = []
    for c in certs_raw:
        if isinstance(c, dict):
            certs_flat.append(c.get('name', '') + (' — ' + c.get('issuer', '') if c.get('issuer') else ''))
        else:
            certs_flat.append(str(c))

    # Normalise languages: accept list of dicts or list of strings
    langs_raw = cv.get('languages', [])
    langs_flat = []
    for lang in langs_raw:
        if isinstance(lang, dict):
            level = lang.get('level', '')
            langs_flat.append(f"{lang.get('language', '')} ({level})" if level else lang.get('language', ''))
        else:
            langs_flat.append(str(lang))

    tex = TEX_DOC.format(
        name=escape_tex(personal.get('name', cv.get('name', 'Candidate'))),
        title=escape_tex(cv.get('title', meta.get('target_title', ''))),
        location=location_block,
        email_raw=email_raw,
        phone_block=phone_block,
        linkedin_raw=linkedin_raw,
        summary=escape_tex(cv.get('summary', '')),
        skills_line=skills_line,
        experience_section=build_experience_section(cv.get('experience', [])),
        projects_section=build_projects_section(cv.get('projects', [])),
        education_section=build_education_section(edu_list),
        certs_section=build_certs_section(certs_flat),
        languages_line=' \\quad|\\quad '.join(escape_tex(l) for l in langs_flat),
    )

    tex_path = Path(cv_json_path).with_suffix('.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex)
    print(f"  LaTeX → {tex_path.name}", end='')

    if compile_pdf:
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-halt-on-error', tex_path.name],
            capture_output=True, text=True, cwd=str(tex_path.parent),
            timeout=60,
        )
        if result.returncode == 0:
            print(' | PDF ✓')
        else:
            print(' | PDF ✗ (check .log)')
    else:
        print()

def render_all(compile_pdf=True):
    from config_loader import get_project_root
    cv_dir = get_project_root() / "output" / "tailored_cvs"
    json_files = sorted(cv_dir.glob('*_tailored.json'))
    print(f"Rendering {len(json_files)} tailored CVs...\n")
    for p in json_files:
        render_cv(p, compile_pdf=compile_pdf)
    print(f"\nAll done. Check output/tailored_cvs/ for .tex and .pdf files.")

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--no-pdf', action='store_true', help='Skip xelatex compile, output .tex only')
    args = p.parse_args()
    render_all(compile_pdf=not args.no_pdf)
