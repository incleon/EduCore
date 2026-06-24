import { BookOpen, Building2, CalendarCheck2, GitBranch, GraduationCap, History, Layers3, Library, ListTree, ReceiptIndianRupee, ScrollText, Shapes, UserCog, UsersRound } from 'lucide-react'

export const resourceConfigs = [
  {
    slug: 'students', label: 'Students', eyebrow: 'People', icon: GraduationCap,
    endpoint: '/api/students', permission: 'view_students', description: 'Enrollment, cohorts and student records.',
    columns: [['student_id', 'Student ID'], ['user.full_name', 'Student'], ['department.name', 'Department'], ['course.name', 'Course'], ['branch.name', 'Branch'], ['semester', 'Semester'], ['status', 'Status']],
  },
  {
    slug: 'teachers', label: 'Faculty', eyebrow: 'People', icon: UsersRound,
    endpoint: '/api/teachers', permission: 'manage_teachers', description: 'Administrator-only faculty directory and account management.',
    columns: [['faculty_id', 'Faculty ID'], ['user.full_name', 'Faculty member'], ['department.name', 'Department'], ['branch.course.name', 'Course'], ['branch.name', 'Branch'], ['designation', 'Designation']],
  },
  {
    slug: 'departments', label: 'Departments', eyebrow: 'Academics', icon: Building2,
    endpoint: '/api/departments', permission: 'view_departments', description: 'Academic departments, courses and leadership.',
    columns: [['code', 'Code'], ['name', 'Department'], ['hod.user.full_name', 'HOD'], ['description', 'Description']],
  },
  {
    slug: 'courses', label: 'Courses', eyebrow: 'Academics', icon: BookOpen,
    endpoint: '/api/courses', permission: 'view_departments', description: 'Programs, duration and curriculum structure.',
    columns: [['code', 'Code'], ['name', 'Course'], ['department.name', 'Department'], ['duration_years', 'Duration'], ['description', 'Description']],
  },
  {
    slug: 'branches', label: 'Branches', eyebrow: 'Academics', icon: GitBranch,
    endpoint: '/api/academic/branches', permission: 'view_academic_structure', description: 'Optional branches and specializations within programs.',
    columns: [['code', 'Code'], ['name', 'Branch / specialization'], ['department.name', 'Department'], ['course.name', 'Program'], ['description', 'Description']],
  },
  {
    slug: 'curricula', label: 'Curricula', eyebrow: 'Academics', icon: Layers3,
    endpoint: '/api/academic/curricula', permission: 'view_academic_structure', description: 'Stable curriculum identities for programs and optional branches.',
    columns: [['code', 'Code'], ['name', 'Curriculum'], ['department.name', 'Department'], ['course.name', 'Program'], ['branch.name', 'Branch'], ['description', 'Description']],
  },
  {
    slug: 'curriculum-versions', label: 'Curriculum versions', eyebrow: 'Academics', icon: History,
    endpoint: '/api/academic/curriculum-versions', permission: 'view_academic_structure', description: 'Batch-locked regulations and effective-year versions.',
    columns: [['version_code', 'Version'], ['title', 'Regulation'], ['curriculum.name', 'Curriculum'], ['effective_year', 'Effective year'], ['applicable_batch_start', 'First batch'], ['status', 'Status']],
  },
  {
    slug: 'semesters', label: 'Semesters', eyebrow: 'Academics', icon: ListTree,
    endpoint: '/api/academic/semesters', permission: 'view_academic_structure', description: 'Semester definitions inside each curriculum version.',
    columns: [['number', 'Number'], ['name', 'Semester'], ['curriculum_version.title', 'Curriculum version'], ['minimum_credits', 'Min credits'], ['maximum_credits', 'Max credits']],
  },
  {
    slug: 'sections', label: 'Sections', eyebrow: 'Academics', icon: Shapes,
    endpoint: '/api/academic/sections', permission: 'view_academic_structure', description: 'Program, branch and semester-specific student sections.',
    columns: [['code', 'Code'], ['department.name', 'Department'], ['course.name', 'Program'], ['branch.name', 'Branch'], ['semester_number', 'Semester'], ['academic_year', 'Academic year'], ['capacity', 'Capacity']],
  },
  {
    slug: 'subjects', label: 'Subjects', eyebrow: 'Academics', icon: ScrollText,
    endpoint: '/api/subjects', permission: 'view_subjects', description: 'Subject catalogue and faculty ownership.',
    columns: [['code', 'Code'], ['name', 'Subject'], ['subject_type.code', 'Classification'], ['department.name', 'Owning department'], ['credits', 'Credits']],
  },
  {
    slug: 'curriculum-subjects', label: 'Curriculum subjects', eyebrow: 'Learning', icon: Layers3,
    endpoint: '/api/academic/curriculum-subjects', permission: 'view_academic_structure', description: 'Common, branch and elective subject allocations without duplication.',
    columns: [['subject.code', 'Code'], ['subject.name', 'Subject'], ['subject.type', 'Classification'], ['semester.number', 'Semester'], ['branch.name', 'Branch scope'], ['is_mandatory', 'Mandatory']],
  },
  {
    slug: 'elective-groups', label: 'Elective groups', eyebrow: 'Learning', icon: Shapes,
    endpoint: '/api/academic/elective-groups', permission: 'view_academic_structure', description: 'Choice groups and elective selection limits.',
    columns: [['code', 'Code'], ['name', 'Elective group'], ['semester.name', 'Semester'], ['minimum_choices', 'Minimum'], ['maximum_choices', 'Maximum']],
  },
  {
    slug: 'faculty-assignments', label: 'Faculty assignments', eyebrow: 'Learning', icon: UserCog,
    endpoint: '/api/academic/faculty-assignments', permission: 'view_academic_structure', description: 'Section and academic-year-specific teaching allocations.',
    columns: [['teacher.name', 'Faculty'], ['subject.code', 'Subject'], ['section.code', 'Section'], ['academic_year', 'Academic year'], ['role', 'Role']],
  },
  {
    slug: 'attendance', label: 'Attendance', eyebrow: 'Learning', icon: CalendarCheck2,
    endpoint: '/api/attendance', permission: 'view_attendance', description: 'Daily attendance and participation records.',
    columns: [['date', 'Date'], ['student.user.full_name', 'Student'], ['subject.name', 'Subject'], ['status', 'Status']],
  },
  {
    slug: 'marks', label: 'Marks', eyebrow: 'Learning', icon: ScrollText,
    endpoint: '/api/marks', permission: 'view_marks', description: 'Assessments, scores and academic outcomes.',
    columns: [['student.user.full_name', 'Student'], ['subject.name', 'Subject'], ['exam_type', 'Assessment'], ['marks_obtained', 'Score'], ['max_marks', 'Maximum']],
  },
  {
    slug: 'fees', label: 'Fees', eyebrow: 'Operations', icon: ReceiptIndianRupee,
    endpoint: '/api/fees', permission: 'view_fees', description: 'Fee schedules, collections and outstanding balances.',
    columns: [['student.user.full_name', 'Student'], ['fee_type', 'Type'], ['amount', 'Amount'], ['paid_amount', 'Paid'], ['due_date', 'Due date'], ['status', 'Status']],
  },
  {
    slug: 'library', label: 'Library', eyebrow: 'Operations', icon: Library,
    endpoint: '/api/library/books', permission: 'view_library', description: 'Catalogue availability and lending inventory.',
    columns: [['isbn', 'ISBN'], ['title', 'Title'], ['author', 'Author'], ['category', 'Category'], ['available_copies', 'Available']],
  },
]

export const getValue = (record, path) => path.split('.').reduce((value, key) => value?.[key], record)
