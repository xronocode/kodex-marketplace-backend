import os
import re

directory = 'app'

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # move from typing import Optional after from __future__ import annotations
    if 'from typing import Optional' in content and 'from __future__ import annotations' in content:
        
        # remove all from typing import Optional
        content = re.sub(r'^from typing import Optional\n', '', content, flags=re.MULTILINE)
        
        # inject it after from __future__ import annotations
        content = re.sub(r'^(from __future__ import annotations\n+)', r'\1from typing import Optional\n', content, count=1, flags=re.MULTILINE)
        
    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))

print("Done fixing FUTURE annotations.")
