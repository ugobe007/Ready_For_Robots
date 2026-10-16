"""Offline check: the rule table's class is one the frozen answer key accepts.

Feed each row's own expected facts. Never edit the key to fit the table.
"""

import json
import sys
from pathlib import Path

from app.services.robot_understanding_v1.class_rules import assign_class

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEYS = (
    ROOT / "tests/fixtures/robot_benchmark_set.v2.json",
    ROOT / "tests/fixtures/robot_holdout_set.v1.json",
    ROOT / "tests/fixtures/robot_holdout_set.v2.json",
    ROOT / "tests/fixtures/robot_oem_richtech_set.v1.json",
)


def check(paths: list[Path]) -> tuple[int, int, list[tuple]]:
    ok = tot = 0
    bad = []
    for path in paths:
        data = json.loads(path.read_text())
        items = data.get("products") or data.get("robots") or []
        for row in items:
            expected = row.get("primary_class_ok") or []
            functions = row.get("functions_required") or []
            if not expected or not functions:
                continue
            industries = (row.get("industries_required") or []) + (row.get("industries_any") or [])
            forms = row.get("form_ok") or [None]
            assigned, rule_id = assign_class(functions[0], industries, forms[0])[:2]
            tot += 1
            if assigned in expected:
                ok += 1
            else:
                bad.append(
                    (
                        path.name,
                        row.get("id"),
                        row.get("target_product"),
                        functions[0],
                        sorted(set(industries)),
                        forms[0],
                        assigned,
                        rule_id,
                        expected,
                    )
                )
    return ok, tot, bad


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] if argv else list(DEFAULT_KEYS)
    ok, tot, bad = check(paths)
    print(f"{ok}/{tot} rows: rule class is in primary_class_ok")
    for row in bad:
        print(" MISMATCH", row)
    return 0 if ok == tot and tot else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
