#!/usr/bin/env python3
"""Fail when repository text files contain common credential formats."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ALLOWLIST_VALUES = {
    "replace-with-a-strong-password",
    "replace-with-a-different-strong-password",
    "replace-with-a-strong-grafana-password",
    "city_dev_password",
    "ci-postgres-password",
    "ci-redis-password",
    "ci-grafana-password",
    "smoke-postgres-password",
    "smoke-redis-password",
    "smoke-grafana-password",
    "drill-postgres-password",
    "drill-redis-password",
    "drill-grafana-password",
    "redis_password",
    "secret",
    "file-secret",
}

PATTERNS = {
    "GitHub token": re.compile(r"\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}\b"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Credentialed database URL": re.compile(r"\bpostgres(?:ql)?(?:\+psycopg2)?://[^:\s]+:([^@\s]+)@"),
    "Credentialed Redis URL": re.compile(r"\bredis://:([^@\s]+)@"),
    "Env password": re.compile(r"(?m)^\s*(?:POSTGRES_PASSWORD|REDIS_PASSWORD|GRAFANA_ADMIN_PASSWORD)\s*=\s*([^\s#]+)"),
    "Suspicious secret file reference": re.compile(
        r"(?m)^\s*(?:POSTGRES_PASSWORD|REDIS_PASSWORD|GRAFANA_ADMIN_PASSWORD|CITY_DATABASE_URL|REDIS_URL)_FILE\s*=\s*([^\s#]+)"
    ),
}


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(raw.decode()) for raw in result.stdout.split(b"\0") if raw]


def _is_allowed_secret(match: re.Match[str]) -> bool:
    if not match.groups():
        return False
    value = match.group(1).strip().strip('"').strip("'")
    if value in ALLOWLIST_VALUES or value.startswith("${") or value.startswith("$") or value.startswith("str("):
        return True
    if "/" in value or "\\" in value or value.startswith("."):
        return True
    return False


def main() -> int:
    findings: list[str] = []
    for path in repository_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                if _is_allowed_secret(match):
                    continue
                findings.append(f"{path}: possible {label}")

    if findings:
        print("Secret scan failed:")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
