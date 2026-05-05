import os

file_path = r'c:\Proyectos\contafy\empresa\templates\empresa\crear_compra.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Specifically target the problematic line with the space
old_text = 'const prodsRaw = {{ productos_json|default: "[]" | safe }};'
new_text = 'const prodsRaw = {{ productos_json|default:"[]"|safe }};'

if old_text in content:
    new_content = content.replace(old_text, new_text)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement successful.")
else:
    # Try a more flexible search if the specific text isn't found
    import re
    new_content = re.sub(r'productos_json\|default:\s*"\[\]"\s*\|\s*safe', 'productos_json|default:"[]"|safe', content)
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Regex replacement successful.")
    else:
        print("Text not found in file.")
