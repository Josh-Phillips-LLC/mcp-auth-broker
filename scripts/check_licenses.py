from __future__ import annotations

import json
import subprocess
import sys

ALLOWED_KEYWORDS = (
    "mit",
    "bsd",
    "apache",
    "isc",
    "python software foundation",
)
DISALLOWED_KEYWORDS = ("gpl", "agpl", "lgpl", "copyleft")


def main() -> int:
    completed = subprocess.run(
        ["pip-licenses", "--format=json", "--with-system"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print("license scan failed to execute", file=sys.stderr)
        print(completed.stderr, file=sys.stderr)
        return 1

    packages = json.loads(completed.stdout)
    violations: list[str] = []

    for package in packages:
        name = str(package.get("Name", ""))
        license_name = str(package.get("License", "")).strip()
        normalized = license_name.lower()

        if name == "mcp-auth-broker" and not license_name:
            continue

        if any(keyword in normalized for keyword in DISALLOWED_KEYWORDS):
            violations.append(f"{name}: disallowed license '{license_name}'")
            continue

        if normalized and any(keyword in normalized for keyword in ALLOWED_KEYWORDS):
            continue

        if name == "mcp-auth-broker" and (not normalized or normalized == "unknown"):
            continue

        violations.append(f"{name}: unapproved license '{license_name}'")

    if violations:
        print("license policy violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("license policy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
