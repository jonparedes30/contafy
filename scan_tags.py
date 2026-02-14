import re
import os

filepath = r'c:\Proyectos\contafy\empresa\templates\empresa\metas.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for multi-line {% if %} or {% for %} or {{ }}
# 1. {% tag ... %} spanning lines
pattern_block = r'(\{%\s*(if|for|elif).*?\n.*?%\})'
# 2. {{ var ... }} spanning lines
pattern_var = r'(\{\{.*?\n.*?\}\})'

matches_block = list(re.finditer(pattern_block, content, re.DOTALL))
matches_var = list(re.finditer(pattern_var, content, re.DOTALL))

if matches_block:
    print(f"Found {len(matches_block)} multi-line block tags:")
    for m in matches_block:
        line_no = content[:m.start()].count('\n') + 1
        print(f"  Line {line_no}: {m.group(1)[:50]}...")

if matches_var:
    print(f"Found {len(matches_var)} multi-line variable tags:")
    for m in matches_var:
        line_no = content[:m.start()].count('\n') + 1
        print(f"  Line {line_no}: {m.group(1)[:50]}...")

if not matches_block and not matches_var:
    print("No multi-line tags found. Safe to start server.")
