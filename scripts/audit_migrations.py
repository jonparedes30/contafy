#!/usr/bin/env python3
"""
audit_migrations.py — Auditoría automática de migraciones Django.

Analiza la cadena de dependencias del directorio empresa/migrations/
y detecta gaps, ramas paralelas y referencias rotas.

Uso:
    python audit_migrations.py
"""
import os
import re
import sys
from pathlib import Path
from collections import defaultdict


MIGRATIONS_DIR = Path(__file__).resolve().parent / 'empresa' / 'migrations'


def parse_migration_file(filepath):
    """Lee un archivo de migración y extrae sus dependencias."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraer dependencias: ('app_label', 'migration_name')
    deps = re.findall(
        r"\(\s*['\"](\w+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
        content
    )

    # Filtrar solo las secciones dentro de `dependencies = [...]`
    dep_section = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if dep_section:
        deps = re.findall(
            r"\(\s*['\"](\w+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
            dep_section.group(1)
        )
    else:
        deps = []

    # Extraer si tiene operaciones vacías
    ops_section = re.search(r'operations\s*=\s*\[(.*?)\]', content, re.DOTALL)
    has_operations = bool(ops_section and ops_section.group(1).strip())

    return {
        'dependencies': deps,
        'has_operations': has_operations,
    }


def discover_migrations(migrations_dir):
    """Descubre todos los archivos de migración y construye el grafo."""
    migrations = {}

    for filename in sorted(os.listdir(migrations_dir)):
        if filename == '__init__.py' or not filename.endswith('.py'):
            continue

        name = filename.replace('.py', '')
        filepath = migrations_dir / filename
        parsed = parse_migration_file(filepath)
        migrations[name] = {
            'filename': filename,
            'filepath': filepath,
            **parsed,
        }

    return migrations


def extract_number(migration_name):
    """Extrae el número de una migración (e.g., '0015_auto_...' -> 15)."""
    match = re.match(r'^(\d+)', migration_name)
    return int(match.group(1)) if match else -1


def audit(migrations):
    """Ejecuta todas las validaciones y retorna resultados."""
    results = []
    all_names = set(migrations.keys())
    numbers = sorted(extract_number(name) for name in all_names)

    # --- Validación 1: Cadena lineal (sin gaps numéricos) ---
    expected = list(range(1, max(numbers) + 1))
    missing_numbers = set(expected) - set(numbers)
    if missing_numbers:
        results.append(('❌', f'Gaps numéricos detectados: faltan migraciones {sorted(missing_numbers)}'))
    else:
        results.append(('✅', f'Cadena numérica completa: 0001 → {max(numbers):04d} ({len(numbers)} migraciones)'))

    # --- Validación 2: Dependencias apuntan a archivos existentes ---
    broken_refs = []
    for name, data in migrations.items():
        for app_label, dep_name in data['dependencies']:
            if app_label == 'empresa' and dep_name not in all_names:
                broken_refs.append((name, dep_name))
    if broken_refs:
        results.append(('❌', f'Referencias rotas encontradas:'))
        for src, dep in broken_refs:
            results.append(('  ❌', f'  {src} → {dep} (NO EXISTE)'))
    else:
        results.append(('✅', 'Todas las dependencias apuntan a archivos existentes'))

    # --- Validación 3: Sin ramas paralelas ---
    # Verificar que cada número tiene exactamente una migración
    number_counts = defaultdict(list)
    for name in all_names:
        num = extract_number(name)
        if num > 0:
            number_counts[num].append(name)

    parallel_branches = {num: names for num, names in number_counts.items() if len(names) > 1}
    if parallel_branches:
        results.append(('❌', 'Ramas paralelas detectadas:'))
        for num, names in sorted(parallel_branches.items()):
            results.append(('  ❌', f'  Número {num:04d}: {", ".join(names)}'))
    else:
        results.append(('✅', 'Sin ramas paralelas (cada número tiene una sola migración)'))

    # --- Validación 4: Cadena de dependencias es lineal ---
    # Cada migración N debe depender de la migración N-1
    chain_issues = []
    sorted_migrations = sorted(migrations.items(), key=lambda x: extract_number(x[0]))

    for i, (name, data) in enumerate(sorted_migrations):
        num = extract_number(name)
        empresa_deps = [dep for app, dep in data['dependencies'] if app == 'empresa']

        if num == 1:
            # Primera migración no debe depender de otras de empresa
            if empresa_deps:
                chain_issues.append(f'0001 tiene dependencia inesperada de empresa: {empresa_deps}')
            continue

        if not empresa_deps:
            chain_issues.append(f'{name} no tiene dependencia de empresa')
            continue

        # Verificar que la dependencia es la migración anterior
        expected_prev_num = num - 1
        prev_migrations = number_counts.get(expected_prev_num, [])
        if prev_migrations:
            dep_match = any(dep in prev_migrations for dep in empresa_deps)
            if not dep_match:
                chain_issues.append(
                    f'{name} depende de {empresa_deps} pero se esperaba {prev_migrations}'
                )

    if chain_issues:
        results.append(('❌', 'Problemas en cadena de dependencias:'))
        for issue in chain_issues:
            results.append(('  ❌', f'  {issue}'))
    else:
        results.append(('✅', 'Cadena de dependencias perfectamente lineal'))

    # --- Validación 5: Verificaciones específicas solicitadas ---
    # 0015 depende de 0014_gap_repair
    mig_0015 = migrations.get('0015_auto_20250822_1526', {})
    deps_0015 = [dep for app, dep in mig_0015.get('dependencies', []) if app == 'empresa']
    if '0014_gap_repair' in deps_0015:
        results.append(('✅', '0015 depende correctamente de 0014_gap_repair'))
    else:
        results.append(('❌', f'0015 NO depende de 0014_gap_repair (deps: {deps_0015})'))

    # 0021 depende de 0020_gap_repair
    mig_0021 = migrations.get('0021_add_accounting_setup', {})
    deps_0021 = [dep for app, dep in mig_0021.get('dependencies', []) if app == 'empresa']
    if '0020_gap_repair' in deps_0021:
        results.append(('✅', '0021 depende correctamente de 0020_gap_repair'))
    else:
        results.append(('❌', f'0021 NO depende de 0020_gap_repair (deps: {deps_0021})'))

    # --- Resumen: gap repairs ---
    gap_repairs = [name for name in all_names if 'gap_repair' in name]
    results.append(('ℹ️', f'Gap repairs encontrados: {len(gap_repairs)} ({", ".join(sorted(gap_repairs))})'))

    # Migraciones vacías (sin operaciones)
    empty = [name for name, data in migrations.items() if not data['has_operations']]
    if empty:
        results.append(('ℹ️', f'Migraciones vacías (operations=[]): {len(empty)}'))

    return results


def main():
    print('=' * 70)
    print('  AUDITORÍA DE MIGRACIONES — empresa/migrations/')
    print('=' * 70)
    print()

    if not MIGRATIONS_DIR.exists():
        print(f'❌ Directorio no encontrado: {MIGRATIONS_DIR}')
        sys.exit(1)

    migrations = discover_migrations(MIGRATIONS_DIR)
    print(f'📂 Migraciones encontradas: {len(migrations)}')
    print()

    # Listar todas en orden
    print('─' * 50)
    print('  CADENA DE MIGRACIONES')
    print('─' * 50)
    for name in sorted(migrations.keys(), key=extract_number):
        data = migrations[name]
        empresa_deps = [dep for app, dep in data['dependencies'] if app == 'empresa']
        dep_str = f' ← {empresa_deps[0]}' if empresa_deps else ' (raíz)'
        ops = '📝' if data['has_operations'] else '📭'
        print(f'  {ops} {name}{dep_str}')

    print()
    print('─' * 50)
    print('  VALIDACIONES')
    print('─' * 50)

    results = audit(migrations)
    for icon, msg in results:
        print(f'  {icon} {msg}')

    # Resultado final
    errors = sum(1 for icon, _ in results if '❌' in icon)
    print()
    print('═' * 50)
    if errors == 0:
        print('  🎉 AUDITORÍA COMPLETADA — SIN ERRORES')
    else:
        print(f'  ⚠️  AUDITORÍA COMPLETADA — {errors} PROBLEMAS ENCONTRADOS')
    print('═' * 50)

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
