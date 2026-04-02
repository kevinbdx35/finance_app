#!/usr/bin/env python3
"""
Incrémentation manuelle de version.

Usage :
  python scripts/bump_version.py patch   # 1.0.4 → 1.0.5  (par défaut)
  python scripts/bump_version.py minor   # 1.0.4 → 1.1.0
  python scripts/bump_version.py major   # 1.0.4 → 2.0.0
"""
import sys
import os

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version_file = os.path.join(repo_root, 'VERSION')

with open(version_file) as f:
    version = f.read().strip()

major, minor, patch = map(int, version.split('.'))
bump = sys.argv[1] if len(sys.argv) > 1 else 'patch'

if bump == 'major':
    major += 1; minor = 0; patch = 0
elif bump == 'minor':
    minor += 1; patch = 0
else:
    patch += 1

new_version = f"{major}.{minor}.{patch}"
with open(version_file, 'w') as f:
    f.write(new_version + '\n')

print(f"{version} → {new_version}")
