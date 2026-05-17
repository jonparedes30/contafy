#!/usr/bin/env python
"""
audit_migrations.py - Auditoria de la cadena de migraciones de empresa/

Valida:
  [OK] / [FAIL] Secuencia numerica sin gaps
  [OK] / [FAIL] Cada migracion depende de la anterior (cadena lineal)
  [OK] / [FAIL] No hay dependencias circulares
  [OK] / [FAIL] No hay referencias a migraciones inexistentes
  [OK] / [FAIL] No hay migraciones huerfanas (nadie las referencia, excepto la ultima)

Uso:
  python audit_migrations.py
  exit code 0 = OK   |   exit code 1 = hay problemas
"""
import ast
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "empresa" / "migrations"
APP_LABEL = "empresa"


def discover_migrations():
    """Lee cada archivo .py de migraciones (excepto __init__.py) y extrae
    numero, nombre y dependencias usando AST (sin ejecutar el modulo)."""
    migrations = {}

    for filepath in sorted(MIGRATIONS_DIR.glob("*.py")):
        if filepath.name == "__init__.py":
            continue

        name = filepath.stem  # e.g. "0001_initial"
        parts = name.split("_", 1)
        if not parts[0].isdigit():
            continue  # saltar archivos que no siguen el patron NNNN_*

        number = int(parts[0])

        # Parsear AST para extraer dependencies
        source = filepath.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=filepath.name)
        except SyntaxError:
            print(f"  [!] No se pudo parsear {filepath.name}")
            continue

        dependencies = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Migration":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "dependencies":
                                # dependencies = [('app', 'name'), ...]
                                if isinstance(item.value, ast.List):
                                    for elt in item.value.elts:
                                        if isinstance(elt, (ast.Tuple, ast.List)) and len(elt.elts) == 2:
                                            dep_app = _get_str(elt.elts[0])
                                            dep_name = _get_str(elt.elts[1])
                                            if dep_app and dep_name:
                                                dependencies.append((dep_app, dep_name))

        migrations[name] = {
            "number": number,
            "file": filepath.name,
            "dependencies": dependencies,
        }

    return migrations


def _get_str(node):
    """Extrae el valor string de un nodo AST Constant/Str."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def validate(migrations):
    """Ejecuta todas las validaciones. Retorna lista de problemas."""
    problems = []
    names = set(migrations.keys())
    numbers = sorted(m["number"] for m in migrations.values())

    # --- 1. Secuencia numerica sin gaps ---
    if numbers:
        expected = list(range(numbers[0], numbers[-1] + 1))
        missing = set(expected) - set(numbers)
        if missing:
            problems.append(
                f"Gaps en secuencia numerica: faltan {sorted(missing)}"
            )
            print(f"  [FAIL] Secuencia numerica: faltan {sorted(missing)}")
        else:
            print(f"  [OK] Secuencia numerica continua ({numbers[0]:04d}-{numbers[-1]:04d})")
    else:
        print("  [!] No se encontraron migraciones")

    # --- 2. Cadena lineal (cada migracion depende de la anterior) ---
    by_number = {m["number"]: name for name, m in migrations.items()}
    broken_chain = []
    for num in numbers:
        if num == numbers[0]:
            continue  # la primera no tiene anterior en la app
        current_name = by_number[num]
        prev_name = by_number.get(num - 1)
        if prev_name is None:
            continue  # gap ya reportado arriba

        deps_empresa = [
            dep_name for app, dep_name in migrations[current_name]["dependencies"]
            if app == APP_LABEL
        ]
        if prev_name not in deps_empresa:
            broken_chain.append((current_name, prev_name))

    if broken_chain:
        for curr, prev in broken_chain:
            problems.append(f"{curr} no depende de {prev}")
            print(f"  [FAIL] Cadena rota: {curr} no depende de {prev}")
    else:
        print("  [OK] Cadena de dependencias lineal correcta")

    # --- 3. Dependencias circulares ---
    # Construir grafo y detectar ciclos con DFS
    graph = {}
    for name, info in migrations.items():
        deps_in_app = [
            dep_name for app, dep_name in info["dependencies"]
            if app == APP_LABEL
        ]
        graph[name] = deps_in_app

    has_cycle, cycle_path = _detect_cycle(graph)
    if has_cycle:
        problems.append(f"Dependencia circular detectada: {' -> '.join(cycle_path)}")
        print(f"  [FAIL] Dependencia circular: {' -> '.join(cycle_path)}")
    else:
        print("  [OK] Sin dependencias circulares")

    # --- 4. Referencias a migraciones inexistentes (como archivo) ---
    missing_refs = []
    for name, info in migrations.items():
        for app, dep_name in info["dependencies"]:
            if app == APP_LABEL and dep_name not in names:
                missing_refs.append((name, dep_name))

    if missing_refs:
        for ref_from, ref_to in missing_refs:
            problems.append(f"{ref_from} referencia migracion inexistente '{ref_to}'")
            print(f"  [FAIL] Referencia inexistente: {ref_from} -> {ref_to}")
    else:
        print("  [OK] Todas las referencias apuntan a archivos existentes")

    # --- 5. Migraciones huerfanas ---
    # Una migracion es huerfana si nadie la tiene como dependencia
    # (excepto la ultima, que naturalmente no es dependida por nadie)
    referenced = set()
    for name, info in migrations.items():
        for app, dep_name in info["dependencies"]:
            if app == APP_LABEL:
                referenced.add(dep_name)

    last_number = max(numbers) if numbers else 0
    orphans = []
    for name, info in migrations.items():
        if info["number"] == last_number:
            continue  # la ultima no necesita ser referenciada
        if name not in referenced:
            orphans.append(name)

    if orphans:
        for orphan in orphans:
            problems.append(f"Migracion huerfana: {orphan} (nadie depende de ella)")
            print(f"  [FAIL] Huerfana: {orphan}")
    else:
        print("  [OK] Sin migraciones huerfanas")

    return problems


def _detect_cycle(graph):
    """Detecta ciclos en un grafo dirigido con DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue  # referencia externa, ignorar
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                return True, path[cycle_start:] + [neighbor]
            if color[neighbor] == WHITE:
                found, cycle = dfs(neighbor, path)
                if found:
                    return True, cycle
        path.pop()
        color[node] = BLACK
        return False, []

    for node in graph:
        if color[node] == WHITE:
            found, cycle = dfs(node, [])
            if found:
                return True, cycle

    return False, []


def main():
    print("=" * 60)
    print("  AUDITORIA DE MIGRACIONES - empresa/migrations/")
    print("=" * 60)
    print()

    if not MIGRATIONS_DIR.is_dir():
        print(f"  [FAIL] Directorio no encontrado: {MIGRATIONS_DIR}")
        sys.exit(1)

    migrations = discover_migrations()
    print(f"  [*] {len(migrations)} migraciones encontradas\n")

    problems = validate(migrations)

    print()
    print("-" * 60)
    if problems:
        print(f"RESULTADO: [FAIL] {len(problems)} problema(s) encontrado(s)")
        for i, p in enumerate(problems, 1):
            print(f"  {i}. {p}")
        sys.exit(1)
    else:
        print("RESULTADO: [OK] MIGRACIONES OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
