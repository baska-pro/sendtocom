#!/usr/bin/env python3
"""Build a version-checked source ZIP and SHA-256 checksum for GitHub Releases."""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "SendToCom.py", "README.md", "LICENSE", "SECURITY.md", "CHANGELOG.md",
    "docs/INSTALLATION.md", "docs/TROUBLESHOOTING.md",
    "docs/ARCHITECTURE.md", "assets/banner.svg", "assets/logo.svg",
]


def source_version() -> str:
    tree = ast.parse((ROOT / "SendToCom.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "VERSION" for t in node.targets):
                value = ast.literal_eval(node.value)
                if isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+", value):
                    return value
    raise ValueError("Missing or invalid VERSION in SendToCom.py")


def validate(tag: str | None = None) -> str:
    version = source_version()
    missing = [p for p in FILES if not (ROOT / p).is_file()]
    if missing:
        raise FileNotFoundError("Missing release files: " + ", ".join(missing))
    if tag and tag != "v" + version:
        raise ValueError(f"Tag {tag!r} does not match SendToCom.py VERSION v{version}")
    return version


def build(version: str) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"BASKA-SEND-v{version}-source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in FILES:
            info = zipfile.ZipInfo("BASKA-SEND/" + path, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (ROOT / path).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / "SHA256SUMS.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate release metadata only")
    args = parser.parse_args()
    version = validate(os.environ.get("VERSION_TAG"))
    if args.check:
        print(f"Release metadata OK: v{version}")
    else:
        print(f"Created: {build(version)}")


if __name__ == "__main__":
    main()
