import os

collections = {
    "branches", "curricula", "versions", "semesters", "curriculum_subjects",
    "elective_groups", "sections", "faculty_assignments", "student_elections",
    "assignments", "submissions", "students", "faculty", "subjects", "programs", "departments",
    "attendances", "marks", "fees", "book_issues", "slots", "notifications"
}

def fix_file(filepath):
    if not os.path.exists(filepath):
        print(f"Not found: {filepath}")
        return
        
    with open(filepath, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    modified = False
    for i, line in enumerate(lines):
        if 'relationship(' in line and 'lazy="selectin"' in line:
            rel_name = line.split('=')[0].strip()
            if rel_name in collections:
                lines[i] = line.replace(', lazy="selectin"', '')
                lines[i] = lines[i].replace(', lazy="joined"', '')
                print(f"Fixed {rel_name} in {os.path.basename(filepath)}")
                modified = True

    if modified:
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

import glob
for f in glob.glob(r'c:\CMS\backend\app\models\*.py'):
    fix_file(f)
