#!/usr/bin/env python3
"""
setup_wizard.py — First-run setup for the Job Application Pipeline.
Asks for your personal details and writes config.json.

Run: python setup_wizard.py
"""
import json, sys
from pathlib import Path

CONFIG_PATH  = Path(__file__).parent / "config.json"
EXAMPLE_PATH = Path(__file__).parent / "config.example.json"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val or default


def ask_multiline(prompt: str) -> str:
    print(f"  {prompt}")
    print("  (type your description, press Enter twice when done)")
    lines = []
    blank_count = 0
    while True:
        line = input("  > ")
        if line == "":
            blank_count += 1
            if blank_count >= 2 and lines:
                break
        else:
            blank_count = 0
            lines.append(line)
    return " ".join(lines).strip()


def main():
    print()
    print("=" * 55)
    print("  Job Application Pipeline — First-Run Setup")
    print("=" * 55)
    print()
    print("  This wizard creates config.json with your details.")
    print("  Your data stays local — config.json is gitignored.")
    print()

    if CONFIG_PATH.exists():
        answer = ask("config.json already exists. Overwrite? (y/N)", "n")
        if answer.lower() != "y":
            print("\n  Aborted. Existing config.json is unchanged.")
            sys.exit(0)
        print()

    with open(EXAMPLE_PATH, encoding="utf-8") as f:
        config = json.load(f)

    # ── Personal details ──────────────────────────────────────
    print("── Personal Details ──────────────────────────────────")
    config["user"]["name"]             = ask("Full name")
    config["user"]["email"]            = ask("Email address")
    config["user"]["phone"]            = ask("Phone (with country code, e.g. +966 50 000 0000)")
    config["user"]["linkedin"]         = ask("LinkedIn URL (e.g. linkedin.com/in/yourprofile)")
    config["user"]["location_current"] = ask("Current city/country (e.g. Jazan, Saudi Arabia)")
    config["user"]["location_target"]  = ask("Target job location (e.g. Riyadh, Saudi Arabia)")
    config["user"]["gpa"]              = ask("GPA (e.g. 4.87/5.00) — leave blank to omit", "")
    config["user"]["grad_year"]        = ask("Graduation year", "2025")
    ccna = ask("CCNA certified? (y/N)", "n")
    config["user"]["ccna"] = ccna.lower() == "y"

    # ── Projects ──────────────────────────────────────────────
    print()
    print("── Projects ──────────────────────────────────────────")
    print("  Describe each project in 2–3 sentences with metrics.")
    print()

    try:
        n_str = ask("How many projects to add", "2")
        n_projects = int(n_str)
    except ValueError:
        n_projects = 2

    config["projects"] = {}
    keys = []
    for i in range(n_projects):
        print()
        key  = ask(f"Project {i + 1} key (short slug, e.g. 'tasi' or 'webapp')")
        if not key:
            key = f"project{i + 1}"
        desc = ask_multiline(f"Project {i + 1} description:")
        config["projects"][key] = desc
        keys.append(key)

    print()
    coop = ask("Describe your internship/co-op (leave blank to skip)", "")
    if coop:
        config["projects"]["coop"] = coop
        keys.append("coop")

    # ── Role → project mapping ─────────────────────────────────
    print()
    print("── Role → Project Mapping ────────────────────────────")
    print(f"  Available keys: {', '.join(keys)}")
    print("  For each role type, enter comma-separated project keys (in priority order).")
    print()

    default_keys = ",".join(keys[:2]) if len(keys) >= 2 else ",".join(keys)
    for role in ["networking", "security", "software", "data", "sales", "support", "general"]:
        val = ask(f"{role}", default_keys)
        config["role_project_map"][role] = [k.strip() for k in val.split(",") if k.strip()]

    # ── Hunter.io (optional) ───────────────────────────────────
    print()
    print("── Optional: Hunter.io Email Enrichment ──────────────")
    print("  Hunter.io finds recruiter emails by company domain.")
    print("  Free tier: 25 searches/month. Get a key at hunter.io")
    print()
    hunter_key = ask("Hunter.io API key (leave blank to skip)", "")
    config["hunterio_api_key"] = hunter_key

    # ── Write ──────────────────────────────────────────────────
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 55)
    print(f"  config.json written to {CONFIG_PATH.name}")
    print()
    print("  Next steps:")
    print("    python src/pipeline.py --step parse   # parse your CV")
    print("    python src/pipeline.py                # run full pipeline")
    print("    python src/pipeline.py --help         # see all options")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()
