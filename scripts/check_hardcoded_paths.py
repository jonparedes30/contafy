#!/usr/bin/env python3
"""Check templates for hard-coded '/empresa/' paths that bypass Django namespacing.

Exits with code 1 if any matches are found. Meant to be called from a git pre-commit hook.
"""
import sys
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATES_DIR = os.path.join(ROOT, 'empresa', 'templates')

pattern = re.compile(r"['\"]?/empresa/[^'\"\s]*['\"]?")

def scan():
    findings = []
    for dirpath, _, filenames in os.walk(TEMPLATES_DIR):
        for fn in filenames:
            if not fn.endswith(('.html', '.txt', '.htm')):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if '/empresa/' in line and pattern.search(line):
                            findings.append((path, i, line.strip()))
            except Exception:
                # ignore unreadable files
                continue
    return findings

def main():
    findings = scan()
    if findings:
        print('Hard-coded /empresa/ paths detected in templates:')
        for path, lineno, line in findings:
            print(f'  {path}:{lineno}: {line}')
        print('\nUse {% url %} with the `empresa` namespace instead. Commit blocked.')
        return 1
    print('No hard-coded /empresa/ paths found.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
