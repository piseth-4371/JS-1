"""Experiment journal: checks docs/experiments.json against git and writes docs/experiment_journal.md.

For every experiment it checks that the rules file was committed BEFORE the first commit of each result report.
It never runs a test and never changes a result.

    .\\.venv\\Scripts\\python scripts\\experiment_journal.py          # check + write the page
    .\\.venv\\Scripts\\python scripts\\experiment_journal.py --check  # check only (exit 1 on a problem)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "docs" / "experiments.json"
PAGE = REPO / "docs" / "experiment_journal.md"
KINDS = {"strategy test", "filter", "measurement", "execution check"}
OUTCOMES = {"fail": "Failed", "pass": "Passed", "inconclusive": "Inconclusive", "incomplete": "In progress (no verdict)",
            "measured": "Measured (no pass/fail)"}
REQUIRED = ("id", "date", "kind", "title", "question", "rules", "rules_commit", "data", "evaluations", "outcome",
            "result", "reports")


class Git:
    def __init__(self, repo: Path = REPO):
        self.repo = repo

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)

    def resolve(self, rev: str) -> str | None:
        p = self._run("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
        return p.stdout.strip() or None

    def first_commit(self, path: str) -> str | None:
        lines = self._run("log", "--diff-filter=A", "--format=%H", "--", path).stdout.split()
        return lines[-1] if lines else None

    def is_ancestor(self, a: str, b: str) -> bool:
        return self._run("merge-base", "--is-ancestor", a, b).returncode == 0

    def exists(self, path: str) -> bool:
        return (self.repo / path).is_file()


def check(entries: list[dict], git) -> tuple[list[str], dict[str, str]]:
    """Returns (problems, pre-registration status per id). A problem means the journal cannot be trusted as written."""
    problems, status = [], {}
    ids = Counter(e.get("id") for e in entries)
    for e in entries:
        eid = e.get("id", "?")
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            problems.append(f"{eid}: missing {', '.join(missing)}")
            continue
        if ids[eid] > 1:
            problems.append(f"{eid}: duplicate id")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e["date"])):
            problems.append(f"{eid}: date must be YYYY-MM-DD")
        if e["kind"] not in KINDS:
            problems.append(f"{eid}: unknown kind '{e['kind']}'")
        if e["outcome"] not in OUTCOMES:
            problems.append(f"{eid}: unknown outcome '{e['outcome']}'")
        if not isinstance(e["evaluations"], int) or e["evaluations"] < 0:
            problems.append(f"{eid}: evaluations must be a whole number >= 0")
        if not e["reports"] and e["outcome"] != "incomplete":
            problems.append(f"{eid}: a finished experiment needs a report")
        for p in e["reports"] + ([e["rules"]] if e["rules"] else []):
            if not git.exists(p):
                problems.append(f"{eid}: file not found: {p}")
        if bool(e["rules"]) != bool(e["rules_commit"]):
            problems.append(f"{eid}: rules and rules_commit must be given together")
        if e["outcome"] == "pass" and not e["rules_commit"]:
            problems.append(f"{eid}: a pass needs rules committed before the result")
        if not e["rules_commit"]:
            status[eid] = "no"
            continue
        rc = git.resolve(e["rules_commit"])
        if rc is None:
            problems.append(f"{eid}: rules commit {e['rules_commit']} not found")
            status[eid] = "unknown"
            continue
        if git.first_commit(e["rules"]) != rc:
            problems.append(f"{eid}: {e['rules']} was not first added in commit {e['rules_commit']}")
        late, pending = [], []
        for p in e["reports"]:
            r = git.first_commit(p)
            if r is None:
                pending.append(p)
            elif r == rc or not git.is_ancestor(rc, r):
                late.append(p)
        if late:
            problems.append(f"{eid}: rules were not committed before {', '.join(late)}")
        status[eid] = "yes, before results" if not pending else "yes; result not committed yet"
    return problems, status


def render(entries: list[dict], status: dict[str, str], problems: list[str]) -> str:
    es = sorted(entries, key=lambda e: (e["date"], e["id"]))
    judged = [e for e in es if e["kind"] in ("strategy test", "filter")]
    evals = sum(e["evaluations"] for e in es)
    passes = sum(e["outcome"] == "pass" for e in es)
    md = ["# Experiment journal", "",
          f"Made by `backend/scripts/experiment_journal.py` on {date.today()} from `docs/experiments.json`. "
          "Every experiment is listed, including every failure. Edit the JSON file, never this page.", "",
          "## How to read it", "",
          "- **Pre-registered** means the rules and pass mark were committed to git *before* the result existed. The script "
          "checks this against git history. \"no\" means the rules were not written down first, so treat that result with "
          "extra caution.",
          "- **Evaluations** counts how many times a strategy was judged against a pass mark. Each one is another chance for "
          "luck to look like skill, which is why the pass mark has to be strict.",
          "- A pass would only make a strategy eligible for one final test on the locked 2025+ data, and only with the "
          "owner's separate approval.", "",
          "## Summary", "",
          f"- Experiments: **{len(es)}** ({len(judged)} strategy tests or filters, {len(es) - len(judged)} measurements or checks).",
          f"- Strategy evaluations so far: **{evals}**. Passed: **{passes}**.",
          f"- Outcomes: " + ", ".join(f"{OUTCOMES[k]} {v}" for k, v in Counter(e["outcome"] for e in es).items()) + ".",
          f"- Journal check: **{'OK' if not problems else f'{len(problems)} problem(s)'}**."]
    if problems:
        md += [""] + [f"  - {p}" for p in problems]
    md += ["", "| id | date | experiment | kind | pre-registered | evaluations | outcome |", "|---|---|---|---|---|---:|---|"]
    md += [f"| {e['id']} | {e['date']} | {e['title']} | {e['kind']} | {status.get(e['id'], '?')} | {e['evaluations']} | "
           f"{OUTCOMES.get(e['outcome'], e['outcome'])} |" for e in es]
    md += ["", "## Details"]
    for e in es:
        rules = f"`{e['rules']}` (commit {e['rules_commit']})" if e["rules"] else "not written down before the test"
        md += ["", f"### {e['id']} — {e['title']}", "",
               f"- **Question:** {e['question']}",
               f"- **Rules:** {rules}",
               f"- **Data:** {e['data']}",
               f"- **Outcome:** {OUTCOMES.get(e['outcome'], e['outcome'])}. {e['result']}",
               f"- **Report:** " + ", ".join(f"`{p}`" for p in e["reports"])]
    md += ["", "## Adding a new experiment", "",
           "1. Write the rules and pass mark in `docs/<name>_preregistration.md` and commit it *before* running anything.",
           "2. Add an entry to `docs/experiments.json` with `\"outcome\": \"incomplete\"` and that commit as `rules_commit`.",
           "3. Run the test, commit the report, then update `outcome` and `result`, including when it fails.",
           "4. Run `.\\.venv\\Scripts\\python scripts\\experiment_journal.py` from `backend`."]
    return "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="check only, do not write the page")
    a = ap.parse_args()
    entries = json.loads(REGISTRY.read_text(encoding="utf-8"))
    problems, status = check(entries, Git())
    for p in problems:
        print("PROBLEM:", p)
    print(f"{len(entries)} experiments, {len(problems)} problem(s)")
    if not a.check:
        PAGE.write_text(render(entries, status, problems), encoding="utf-8")
        print("->", PAGE)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
