import os

path = r'c:\Proyectos\contafy\empresa\templates\empresa\crear_compra.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix space in default filter
old_line = 'const prodsRaw = {{ productos_json|default: "[]" | safe }};'
new_line = 'const prodsRaw = {{ productos_json|default:"[]"|safe }};'

if old_line in content:
    new_content = content.replace(old_line, new_line)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Fixed spaces in crear_compra.html")
else:
    # Try more liberal match just in case
    import re
    new_content, count = re.subn(r'productos_json\s*\|\s*default\s*:\s*"\[\]"\s*\|\s*safe', 'productos_json|default:"[]"|safe', content)
    if count > 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"SUCCESS: Fixed {count} instances via regex")
    else:
        print("FAILURE: Snippet not found in file")
