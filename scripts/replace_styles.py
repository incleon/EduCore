import os
import re

search_dir = r'c:\CMS\app\templates'
replacements = [
    (r'style="background:\s*var\(--gradient-primary\)[^"]*"', 'class="bg-primary"'),
    (r'style="color:\s*var\(--accent-primary-light\)[^"]*"', 'class="text-primary"'),
    (r'style="background:\s*rgba\(99,\s*102,\s*241[^"]*"', 'class="bg-primary"'),
    (r'style="background:\s*var\(--bg-surface\)[^"]*"', 'class="bg-surface"'),
    (r'style="color:\s*var\(--text-muted\)[^"]*"', 'class="text-muted"'),
    (r'style="background:\s*var\(--gradient-success\)[^"]*"', 'class="bg-success"'),
    (r'#6366f1', '#2d3757'),
    (r'#8b5cf6', '#2d3757'),
    (r'#818cf8', '#3d4f7c'),
    (r'rgba\(99,\s*102,\s*241', 'rgba(45, 55, 87'),
    (r'rgba\(139,\s*92,\s*246', 'rgba(45, 55, 87'),
    (r'var\(--gradient-primary\)', 'var(--color-primary)'),
    (r'var\(--gradient-success\)', 'var(--color-success)'),
    (r'var\(--shadow-glow[^\)]*\)', 'var(--shadow-md)'),
    (r'floatIcon', ''),
    (r'bgPulse', ''),
    (r'fadeInUp', 'fadeIn'),
    (r'fadeInDown', 'fadeIn'),
    (r'translateY\(-4px\)', ''),
    (r'translateY\(-2px\)', ''),
    (r'translateX\(4px\)', ''),
    (r'-webkit-text-fill-color:\s*transparent;?', ''),
    (r'-webkit-background-clip:\s*text;?', ''),
    (r'backdrop-filter[^\;]*;?', ''),
    (r'-webkit-backdrop-filter[^\;]*;?', ''),
    (r'data-bs-theme="dark"', ''),
    (r'#0f1117', '#f5f6f8'),
    (r'#0d1017', '#2d3757'),
    (r'#161a25', '#f5f6f8'),
    (r'#1a1f2e', '#ffffff')
]

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            original_content = content
            for pattern, repl in replacements:
                content = re.sub(pattern, repl, content)
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Updated {path}')
