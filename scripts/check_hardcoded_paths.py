#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
"""
check_hardcoded_paths.py — Pre-commit hook.

Verifica que los templates no contengan rutas hardcodeadas del tipo
/empresa/ que deberían usar {% url %} u otras referencias dinámicas.

Retorna:
    0 — Sin problemas encontrados
    1 — Se encontraron rutas hardcodeadas
"""
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / 'empresa' / 'templates'

# Patrones que indican rutas hardcodeadas problemáticas
# Excluimos href="{% url ... %}" y action="{% url ... %}" que son correctos
HARDCODED_PATTERN = re.compile(
    r'''(?:href|action|src)\s*=\s*['"]/empresa/[^{'"]+['"]''',
    re.IGNORECASE,
)

EXCLUDED_PATTERNS = [
    re.compile(r'\{%\s*url\s+'),  # Django url tag
    re.compile(r'\{\{'),           # Django variable
]


def check_file(filepath: Path) -> list[tuple[int, str]]:
    """Retorna lista de (línea, contenido) con problemas."""
    issues = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return issues

    for lineno, line in enumerate(content.splitlines(), start=1):
        if HARDCODED_PATTERN.search(line):
            # Excluir si contiene un tag Django en la misma línea
            if not any(p.search(line) for p in EXCLUDED_PATTERNS):
                issues.append((lineno, line.strip()))
    return issues


def main() -> int:
    if not TEMPLATES_DIR.exists():
        # No hay directorio de templates, nada que revisar
        return 0

    total_issues = 0
    for template_file in TEMPLATES_DIR.rglob('*.html'):
        issues = check_file(template_file)
        if issues:
            rel = template_file.relative_to(ROOT_DIR)
            for lineno, line in issues:
                print(f'  [!] {rel}:{lineno}: {line[:120]}')
            total_issues += len(issues)

    if total_issues:
        print(f'\n[FAIL] {total_issues} ruta(s) hardcodeada(s) encontrada(s).')
        print('   Usa {%% url "nombre_vista" %%} en lugar de rutas directas.')
        return 1

    print('[OK] Sin rutas hardcodeadas detectadas.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
