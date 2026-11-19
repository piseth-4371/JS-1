"""Experiment journal checks (scripts/experiment_journal.py)."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "scripts" / "experiment_journal.py"
spec = importlib.util.spec_from_file_location("experiment_journal", path)
ej = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ej)


class FakeGit:
    """History: rules added in c1, report added in c2 (after c1); c0 is older than both."""
    order = ["c0", "c1", "c2"]

    def __init__(self, added=None, files=None):
        self.added = added if added is not None else {"rules.md": "c1", "report.md": "c2"}
        self.files = files if files is not None else {"rules.md", "report.md"}

    def resolve(self, rev):
        return rev if rev in self.order else None

    def first_commit(self, p):
        return self.added.get(p)

    def is_ancestor(self, a, b):
        return self.order.index(a) <= self.order.index(b)

    def exists(self, p):
        return p in self.files


def entry(**kw):
    e = {"id": "E1", "date": "2026-11-19", "kind": "strategy test", "title": "t", "question": "q", "rules": "rules.md",
         "rules_commit": "c1", "data": "d", "evaluations": 1, "outcome": "fail", "result": "r", "reports": ["report.md"]}
    e.update(kw)
    return e


def test_rules_before_results_is_ok():
    problems, status = ej.check([entry()], FakeGit())
    assert problems == [] and status["E1"] == "yes, before results"


def test_rules_added_after_the_report_is_a_problem():
    problems, _ = ej.check([entry(rules_commit="c2")], FakeGit(added={"rules.md": "c2", "report.md": "c1"}))
    assert problems == ["E1: rules were not committed before report.md"]


def test_rules_and_report_in_the_same_commit_is_a_problem():
    problems, _ = ej.check([entry()], FakeGit(added={"rules.md": "c1", "report.md": "c1"}))
    assert any("not committed before" in p for p in problems)


def test_wrong_rules_commit_is_a_problem():
    problems, _ = ej.check([entry(rules_commit="c0")], FakeGit())
    assert any("not first added in commit c0" in p for p in problems)


def test_a_pass_without_preregistration_is_refused():
    problems, status = ej.check([entry(rules=None, rules_commit=None, outcome="pass")], FakeGit())
    assert any("a pass needs rules" in p for p in problems) and status["E1"] == "no"


def test_uncommitted_report_is_pending_not_a_problem():
    problems, status = ej.check([entry()], FakeGit(added={"rules.md": "c1"}))
    assert problems == [] and status["E1"] == "yes; result not committed yet"


def test_bad_fields_and_missing_files_are_reported():
    problems, _ = ej.check([entry(kind="guess", outcome="win", evaluations=-1, reports=["nope.md"]), entry()], FakeGit())
    text = " ".join(problems)
    for bit in ("unknown kind", "unknown outcome", "evaluations", "file not found: nope.md", "duplicate id"):
        assert bit in text


def test_page_counts_failures_and_evaluations():
    es = [entry(), entry(id="E2", evaluations=7, rules=None, rules_commit=None)]
    md = ej.render(es, {"E1": "yes, before results", "E2": "no"}, [])
    assert "Strategy evaluations so far: **8**. Passed: **0**." in md and "| E2 |" in md and "Failed 2" in md
