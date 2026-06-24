import re
with open('backend/app/services/crud_services.py', 'r', encoding='utf-8') as f:
    content = f.read()

services = {
    'StudentService': '_student_repo',
    'TeacherService': '_teacher_repo',
    'CourseService': '_course_repo',
    'DepartmentService': '_dept_repo',
    'SubjectService': '_subject_repo'
}

for service, repo in services.items():
    pattern = r'(class ' + service + r'\(IService\):.*?\n\n)(?=# --------------------------------------------------------------)'
    
    def replacer(match):
        orig = match.group(1)
        orig = orig.rstrip()
        new_method = f'''

    def delete_all(self) -> int:
        count = 0
        items = self.{repo}.get_all(limit=100000)
        for item in items:
            if self.delete(item.id):
                count += 1
        return count

'''
        return orig + new_method
        
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('backend/app/services/crud_services.py', 'w', encoding='utf-8') as f:
    f.write(content)
