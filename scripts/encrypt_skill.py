#!/usr/bin/env python3
"""
Encrypt plaintext skill file for T029.

Reads a plaintext skill file and encrypts it using Fernet (same mechanism as token_vault).
Writes the ciphertext to backend/app/skills/bd_lead_research.md.enc.

Usage:
    python scripts/encrypt_skill.py [path_to_plaintext_skill]

If no path provided, searches for:
    1. backend/app/skills/bd_lead_research.source.md (preferred source)
    2. BD-Lead-Research-SKILL-v06.md (root fallback)
"""

import sys
import os
from pathlib import Path

# Add backend to path so we can import config + token_vault
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import settings
from app.services.token_vault import encrypt_credentials


def main():
    # Determine which plaintext skill file to encrypt
    source_file = None
    if len(sys.argv) > 1:
        source_file = sys.argv[1]
    else:
        # Search in order: source.md, then root skill file
        candidates = [
            Path(__file__).parent.parent / "backend" / "app" / "skills" / "bd_lead_research.source.md",
            Path(__file__).parent.parent / "BD-Lead-Research-SKILL-v06.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                source_file = str(candidate)
                break

    if not source_file or not Path(source_file).exists():
        print(f"ERROR: Could not find plaintext skill file. Checked: {candidates}")
        sys.exit(1)

    source_path = Path(source_file)
    print(f"Reading plaintext skill from: {source_path}")

    # Read the plaintext skill
    try:
        plaintext = source_path.read_text(encoding="utf-8")
        print(f"Read {len(plaintext)} bytes of plaintext skill")
    except Exception as e:
        print(f"ERROR: Failed to read skill file: {e}")
        sys.exit(1)

    # Encrypt using token_vault's mechanism
    try:
        ciphertext = encrypt_credentials(plaintext)
        print(f"Encrypted to {len(ciphertext)} bytes of ciphertext (base64)")
    except Exception as e:
        print(f"ERROR: Encryption failed: {e}")
        sys.exit(1)

    # Write encrypted file
    output_dir = Path(__file__).parent.parent / "backend" / "app" / "skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "bd_lead_research.md.enc"

    try:
        output_path.write_text(ciphertext, encoding="utf-8")
        print(f"Wrote encrypted skill to: {output_path}")
        print(f"File size: {output_path.stat().st_size} bytes")

        # Verify it's not plaintext by checking first bytes
        first_bytes = ciphertext[:50]
        if first_bytes.startswith("---"):
            print("WARNING: Output looks like plaintext YAML (starts with ---)")
        else:
            print("✓ Encryption confirmed (output is base64/ciphertext, not plaintext)")

        print("\n✓ Skill encryption successful!")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to write encrypted file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
