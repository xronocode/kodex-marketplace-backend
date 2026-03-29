import os
import re

directory = 'app'

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if '| None' not in content:
        return
        
    print(f"Fixing {filepath}...")
    
    # regex to match: Type | None
    # could be string, int, Decimal, date, uuid.UUID, etc.
    # also handle complex types like tuple[list[dict], str | None, int] -> tuple[list[dict], Optional[str], int]
    # actually, the regex `([a-zA-Z0-9_\[\]\.]+) \| None` -> `Optional[\1]` works well for simple types
    # Let's do a somewhat simple approach:
    new_content = re.sub(r'([a-zA-Z0-9_\.]+(?:\[[^\]]*\])?) \| None', r'Optional[\1]', content)
    
    # check if Optional is imported from typing
    if 'Optional' in new_content and 'from typing import ' not in new_content:
        # Just put it under the first import if missing
        new_content = re.sub(r'^(import .*|from .*)$', r'from typing import Optional\n\1', new_content, count=1, flags=re.MULTILINE)
    elif 'Optional' in new_content and 'from typing import ' in new_content and 'Optional' not in re.search(r'from typing import .+', new_content).group(0):
        # Let's just do a brute force search and inject Optional
        pass 
        
    # Better: explicitly find 'from typing import ' and append Optional, or just add a new line `from typing import Optional`
    if 'from typing import Optional' not in new_content and 'import Optional' not in new_content:
        new_content = re.sub(r'(from __future__ import annotations\n+)', r'\1from typing import Optional\n', new_content, count=1)
        if 'from typing import Optional' not in new_content:
            new_content = 'from typing import Optional\n' + new_content
        
    with open(filepath, 'w') as f:
        f.write(new_content)

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))

print("Done fixing types.")
