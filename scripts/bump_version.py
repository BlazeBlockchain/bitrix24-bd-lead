#!/usr/bin/env python3
"""Bump version number in VERSION file."""

import sys
from pathlib import Path


def bump_version(bump_type):
    """Bump version according to type (patch, minor, major)."""
    version_file = Path('VERSION')
    version = version_file.read_text().strip()

    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == 'patch':
        patch += 1
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    new_version = f"{major}.{minor}.{patch}"
    version_file.write_text(new_version + '\n')
    print(f"Bumped {bump_type} version: {version} → {new_version}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 bump_version.py {patch|minor|major}")
        sys.exit(1)
    bump_version(sys.argv[1])
