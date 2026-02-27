#!/usr/bin/env python3
"""
Bump the patch version in version.txt (e.g. 1.0.0 -> 1.0.1, 1.0.1 -> 1.0.2).
Run before creating a new release tag. Usage: python bump_version.py
"""
import os
import re

VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")


def main():
    if not os.path.isfile(VERSION_FILE):
        print("version.txt not found")
        return 1
    with open(VERSION_FILE, "r") as f:
        lines = f.readlines()
    if not lines:
        print("version.txt is empty")
        return 1
    version_line = lines[0].strip()
    # Parse x.y or x.y.z; we only bump the last (patch) number
    parts = re.sub(r"[^0-9.]", "", version_line).split(".")
    parts = [p for p in parts if p]
    if not parts:
        print("Could not parse version:", version_line)
        return 1
    # Ensure we have at least 3 parts (major.minor.patch)
    while len(parts) < 3:
        parts.append("0")
    patch = int(parts[2])
    parts[2] = str(patch + 1)
    new_version = ".".join(parts)
    lines[0] = new_version + "\n"
    with open(VERSION_FILE, "w") as f:
        f.writelines(lines)
    print("Bumped version: %s -> %s" % (version_line, new_version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
