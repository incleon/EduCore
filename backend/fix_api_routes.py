import re

with open('app/routers/api_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'return _format_teacher\(teacher\)se None,.*?    \}', 'return _format_teacher(teacher)', content, flags=re.DOTALL)

with open('app/routers/api_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
