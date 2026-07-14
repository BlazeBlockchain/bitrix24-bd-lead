#!/usr/bin/env python3
"""Sync VERSION file to all component version fields."""

import json
import re
from pathlib import Path


def sync_versions():
    """Read VERSION and update all component files."""
    version_file = Path('VERSION')
    version = version_file.read_text().strip()

    # Update root package.json
    with open('package.json', 'r') as f:
        data = json.load(f)
    data['version'] = version
    with open('package.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✓ root package.json: {version}")

    # Update web/package.json
    with open('web/package.json', 'r') as f:
        data = json.load(f)
    data['version'] = version
    with open('web/package.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✓ web/package.json: {version}")

    # Update extension/manifest.json
    with open('extension/manifest.json', 'r') as f:
        data = json.load(f)
    data['version'] = version
    with open('extension/manifest.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✓ extension/manifest.json: {version}")

    # Update backend/app/config.py APP_VERSION
    config_path = Path('backend/app/config.py')
    content = config_path.read_text()
    new_content = re.sub(
        r'APP_VERSION: str = "[^"]*"',
        f'APP_VERSION: str = "{version}"',
        content
    )
    config_path.write_text(new_content)
    print(f"✓ backend/app/config.py APP_VERSION: {version}")


if __name__ == '__main__':
    sync_versions()
