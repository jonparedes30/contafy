
import re
import os

filepath = r'c:\Proyectos\contafy\empresa\templates\empresa\metas.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

original_content = content

# 1. Fix multi-line {{ ... }} variable tags
# Pattern: {{ [content with newline] }}
# We count {} nesting if possible, but simplest regex is {{ ... }} without nested {{ }} usually.
# Assuming no {{ inside {{ ... }}.
pattern_var = r'(\{\{[^}]*?\n.*?\}\})'

def fix_var(m):
    text = m.group(1)
    # Replace newlines with spaces, strip extra spaces
    cleaned = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
    # Ensure {{ has space after and }} has space before
    if not cleaned.startswith('{{ '):
        cleaned = '{{ ' + cleaned[2:]
    if not cleaned.endswith(' }}'):
        cleaned = cleaned[:-2] + ' }}'
    return cleaned

content_new = re.sub(pattern_var, fix_var, content, flags=re.DOTALL)
if content_new != content:
    print("Fixed some {{ }} tags.")
    content = content_new

# 2. Fix multi-line {% ... %} block tags (if, elif, for, widthratio)
# Pattern: {% (if|elif|for|widthratio) ... \n ... %}
pattern_block = r'(\{%\s*(?:if|elif|for|widthratio)[^%]*?\n.*?%\})'

def fix_block(m):
    text = m.group(1)
    # valid block tags don't have newlines inside the tag itself
    # Replace newlines with spaces
    cleaned = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
    return cleaned

content_new = re.sub(pattern_block, fix_block, content, flags=re.DOTALL)
if content_new != content:
    print("Fixed some {% %} block tags.")
    content = content_new

if content != original_content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("File updated successfully.")
else:
    print("No changes made.")
