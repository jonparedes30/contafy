import os

file_path = r'c:\Proyectos\contafy\empresa\templates\empresa\crear_compra.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_until = -1
for i, line in enumerate(lines):
    if i <= skip_until:
        continue
    
    # Fix the duplicate nested div at line 66-67
    if 'text-start bg-white p-3 rounded border' in line and i + 1 < len(lines) and 'text-start bg-white p-3 rounded border' in lines[i+1]:
        new_lines.append(line)
        skip_until = i + 1 # Skip the duplicate
        continue

    # Fix the missing script tag at line 220
    if '// 1. Datos iniciales (Inventory map)' in line:
        # Check if Quagga is already there (unlikely given previous search)
        found_quagga = False
        for l in new_lines[-5:]:
            if 'quagga.min.js' in l:
                found_quagga = True
                break
        
        if not found_quagga:
            new_lines.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>\n\n')
        
        new_lines.append('<script>\n')
        new_lines.append(line)
        continue
    
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Repair completed.")
