"""
Full CV Tailoring Pipeline

Usage:
  python src/pipeline.py                     # run all steps (default CV)
  python src/pipeline.py --cv my_cv.tex      # use your own CV
  python src/pipeline.py --step intel        # only step: intel
  python src/pipeline.py --step parse
  python src/pipeline.py --step match
  python src/pipeline.py --step tailor
  python src/pipeline.py --step render
  python src/pipeline.py --no-pdf            # skip PDF compilation
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def run_all(cv_path=None, step=None, no_pdf=False, use_llm=False):
    all_steps = ['intel', 'parse', 'match', 'tailor', 'render', 'classify', 'cover', 'track']
    steps = [step] if step else all_steps

    if 'intel' in steps:
        print('\n' + '='*60)
        print('STEP 1: Company Intelligence Map')
        print('='*60)
        from company_intel import run as run_intel
        run_intel()

    if 'parse' in steps:
        print('\n' + '='*60)
        print('STEP 2: Parse Base CV')
        print('='*60)
        from cv_parser import run as run_parse
        run_parse(cv_path=cv_path)

    if 'match' in steps:
        print('\n' + '='*60)
        print('STEP 3: Keyword Match Report')
        print('='*60)
        from keyword_extractor import generate_match_report
        generate_match_report()

    if 'tailor' in steps:
        print('\n' + '='*60)
        print('STEP 4: Tailor CVs Per Job')
        print('='*60)
        from cv_tailor import run_tailor
        run_tailor(use_llm=use_llm)

    if 'render' in steps:
        print('\n' + '='*60)
        print('STEP 5: Render LaTeX / PDF')
        print('='*60)
        from latex_renderer import render_all
        render_all(compile_pdf=not no_pdf)

    if 'classify' in steps:
        print('\n' + '='*60)
        print('STEP 6: Classify Emails (Cybersecurity First)')
        print('='*60)
        from email_classifier import run_classify
        run_classify()

    if 'cover' in steps:
        print('\n' + '='*60)
        print('STEP 7: Generate Cover Emails')
        print('='*60)
        from cover_email_generator import run_cover
        run_cover()

    if 'track' in steps:
        print('\n' + '='*60)
        print('STEP 8: Application Tracker Summary')
        print('='*60)
        from application_tracker import print_summary
        print_summary()

    print('\n' + '='*60)
    print('PIPELINE COMPLETE')
    print('='*60)
    print('Outputs:')
    print('  output/company_map.md              — all 392 companies, sectors, keywords')
    print('  output/company_intel.json          — machine-readable company map')
    print('  output/base_cv.json                — your CV (fill [FILL] elective names)')
    print('  output/match_report.md             — per-job match scores + gaps')
    print('  output/priority_jobs_matched.json  — 29 top jobs with match data')
    print('  output/tailored_cvs/               — 29 tailored JSON + TEX + PDF per job')
    print('  output/email_classified.json       — 1042 emails ranked by sector')
    print('  output/cover_emails/               — cover email draft per job (.txt)')
    print('  output/applications_tracker.json   — sent/pending/replied tracker')
    print()
    print('New steps:')
    print('  python src/pipeline.py --step classify   # re-classify emails')
    print('  python src/pipeline.py --step cover      # regenerate cover emails')
    print('  python src/pipeline.py --step track      # show application status')
    print('  python src/pipeline.py --step tailor --llm  # LLM-powered summaries')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--cv', default=None)
    p.add_argument('--step', default=None,
                   choices=['intel', 'parse', 'match', 'tailor', 'render', 'classify', 'cover', 'track'])
    p.add_argument('--no-pdf', action='store_true')
    p.add_argument('--llm', action='store_true', help='Use Claude API to rewrite CV summaries')
    args = p.parse_args()
    run_all(cv_path=args.cv, step=args.step, no_pdf=args.no_pdf, use_llm=args.llm)
