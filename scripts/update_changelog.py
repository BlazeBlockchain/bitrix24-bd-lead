#!/usr/bin/env python3
"""Update CHANGELOG.md with a new version section."""

from datetime import date
from pathlib import Path


def update_changelog():
    """Add a new version section to CHANGELOG.md."""
    version_file = Path('VERSION')
    version = version_file.read_text().strip()

    changelog_path = Path('CHANGELOG.md')
    content = changelog_path.read_text()

    today = date.today().strftime('%Y-%m-%d')
    new_section = f"""## [{version}] - {today}

### Added
-

### Changed
-

### Fixed
-
"""

    # Insert after ## [Unreleased]
    new_content = content.replace('## [Unreleased]', f'## [Unreleased]\n\n{new_section}', 1)
    changelog_path.write_text(new_content)
    print(f"Updated CHANGELOG.md for {version}")


if __name__ == '__main__':
    update_changelog()
