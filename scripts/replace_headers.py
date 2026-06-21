import os

# Replacements for each file
files_to_update = {
    r'c:\CMS\app\templates\students\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
        <p class="text-muted mb-0" style="font-size:0.85rem;">
            <i class="bi bi-journal-bookmark me-1"></i>Select a course to browse students
        </p>
        {% if 'manage_students' in permissions %}
        <a href="/students/create" class="btn btn-primary">
            <i class="bi bi-plus-lg me-2"></i>Add Student
        </a>
        {% endif %}
    </div>''',
            '''<div class="page-header">
        <div>
            <h1 class="page-heading">Students</h1>
            <p class="page-subheading">Manage enrolled students and their profiles</p>
        </div>
        <div class="page-actions">
            {% if 'manage_students' in permissions %}
            <a href="/students/create" class="btn btn-primary">
                <i class="bi bi-plus me-1"></i> Add Student
            </a>
            {% endif %}
        </div>
    </div>'''
        )
    ],
    r'c:\CMS\app\templates\teachers\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
        <p class="text-muted mb-0" style="font-size:0.85rem;">
            <i class="bi bi-building me-1"></i>Select a department to view teachers
        </p>
        {% if 'manage_teachers' in permissions %}
        <a href="/teachers/create" class="btn btn-primary">
            <i class="bi bi-plus-lg me-2"></i>Add Teacher
        </a>
        {% endif %}
    </div>''',
            '''<div class="page-header">
        <div>
            <h1 class="page-heading">Teachers</h1>
            <p class="page-subheading">Manage faculty members and assignments</p>
        </div>
        <div class="page-actions">
            {% if 'manage_teachers' in permissions %}
            <a href="/teachers/create" class="btn btn-primary">
                <i class="bi bi-plus me-1"></i> Add Teacher
            </a>
            {% endif %}
        </div>
    </div>'''
        )
    ],
    r'c:\CMS\app\templates\courses\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item text-muted">Academics</li>
            <li class="breadcrumb-item active" aria-current="page">Courses</li>
        </ol>
    </nav>
    {% if 'manage_departments' in permissions %}
    <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addCourseOffcanvas">
        <i class="bi bi-plus-lg me-2"></i>Add Course
    </button>
    {% endif %}
</div>''',
            '''<div class="page-header">
    <div>
        <h1 class="page-heading">Courses</h1>
        <p class="page-subheading">Manage academic programs</p>
    </div>
    <div class="page-actions">
        {% if 'manage_departments' in permissions %}
        <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addCourseOffcanvas">
            <i class="bi bi-plus me-1"></i> Add Course
        </button>
        {% endif %}
    </div>
</div>'''
        )
    ],
    r'c:\CMS\app\templates\departments\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item text-muted">Academics</li>
            <li class="breadcrumb-item active" aria-current="page">Departments</li>
        </ol>
    </nav>
    {% if 'manage_departments' in permissions %}
    <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addDepartmentOffcanvas">
        <i class="bi bi-plus-lg me-2"></i>Add Department
    </button>
    {% endif %}
</div>''',
            '''<div class="page-header">
    <div>
        <h1 class="page-heading">Departments</h1>
        <p class="page-subheading">Manage college departments</p>
    </div>
    <div class="page-actions">
        {% if 'manage_departments' in permissions %}
        <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addDepartmentOffcanvas">
            <i class="bi bi-plus me-1"></i> Add Department
        </button>
        {% endif %}
    </div>
</div>'''
        )
    ],
    r'c:\CMS\app\templates\subjects\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item text-muted">Academics</li>
            <li class="breadcrumb-item active" aria-current="page">Subjects</li>
        </ol>
    </nav>
    {% if 'manage_subjects' in permissions %}
    <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addSubjectOffcanvas">
        <i class="bi bi-plus-lg me-2"></i>Add Subject
    </button>
    {% endif %}
</div>''',
            '''<div class="page-header">
    <div>
        <h1 class="page-heading">Subjects</h1>
        <p class="page-subheading">Manage curriculum subjects</p>
    </div>
    <div class="page-actions">
        {% if 'manage_subjects' in permissions %}
        <button class="btn btn-primary shadow-sm" data-bs-toggle="offcanvas" data-bs-target="#addSubjectOffcanvas">
            <i class="bi bi-plus me-1"></i> Add Subject
        </button>
        {% endif %}
    </div>
</div>'''
        )
    ],
    r'c:\CMS\app\templates\attendance\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h5 class="mb-1 text-heading" style="font-weight:700;">Attendance</h5>
        <p class="text-muted mb-0" style="font-size:0.85rem;">View and manage attendance records</p>
    </div>
    {% if 'mark_attendance' in permissions %}
    <a href="/attendance/mark" class="btn btn-primary"><i class="bi bi-plus-lg me-2"></i>Mark Attendance</a>
    {% endif %}
</div>''',
            '''<div class="page-header">
    <div>
        <h1 class="page-heading">Attendance</h1>
        <p class="page-subheading">View and manage attendance records</p>
    </div>
    <div class="page-actions">
        {% if 'mark_attendance' in permissions %}
        <a href="/attendance/mark" class="btn btn-primary">
            <i class="bi bi-plus me-1"></i> Mark Attendance
        </a>
        {% endif %}
    </div>
</div>'''
        )
    ],
    r'c:\CMS\app\templates\marks\list.html': [
        (
            '''<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h5 class="mb-1 text-heading" style="font-weight:700;">Marks &amp; Grades</h5>
        <p class="text-muted mb-0" style="font-size:0.85rem;">View academic performance records</p>
    </div>
    {% if 'upload_marks' in permissions %}
    <a href="/marks/upload" class="btn btn-primary"><i class="bi bi-plus-lg me-2"></i>Upload Marks</a>
    {% endif %}
</div>''',
            '''<div class="page-header">
    <div>
        <h1 class="page-heading">Marks &amp; Grades</h1>
        <p class="page-subheading">View academic performance records</p>
    </div>
    <div class="page-actions">
        {% if 'upload_marks' in permissions %}
        <a href="/marks/upload" class="btn btn-primary">
            <i class="bi bi-plus me-1"></i> Upload Marks
        </a>
        {% endif %}
    </div>
</div>'''
        )
    ]
}

for filepath, replacements in files_to_update.items():
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        for old_str, new_str in replacements:
            content = content.replace(old_str, new_str)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated header in {filepath}")
    else:
        print(f"File not found: {filepath}")
