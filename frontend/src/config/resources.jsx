import { BookOpen, Building2, CalendarCheck2, GitBranch, GraduationCap, History, Layers3, Library, ListTree, ReceiptIndianRupee, ScrollText, Shapes, UserCog, UsersRound, Tags, PenTool, Printer, Bookmark, Users, Wallet, Banknote, Landmark, TrendingDown, WalletCards } from 'lucide-react'
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
    slug: 'fee-structures', label: 'Fee Structures', eyebrow: 'Finance', icon: Landmark,
    endpoint: '/api/finance/fee-structures', permission: 'view_fees', description: 'Define fee amounts by course and year.',
    columns: [['name', 'Name'], ['amount', 'Amount'], ['course.name', 'Course'], ['academic_year', 'Academic Year'], ['semester', 'Semester']],
  },
  {
    slug: 'student-fees', label: 'Invoices', eyebrow: 'Finance', icon: ScrollText,
    endpoint: '/api/finance/student-fees', permission: 'view_fees', description: 'Student fee invoices and balances.',
    columns: [['student.user.full_name', 'Student'], ['title', 'Title'], ['amount', 'Amount'], ['balance', 'Balance'], ['status', 'Status']],
  },
  {
    slug: 'fee-collection', label: 'Point of Sale', eyebrow: 'Finance', icon: WalletCards,
    permission: 'manage_fees', description: 'Collect fees from students.',
    columns: [], // Custom page
  },
  {
    slug: 'payments', label: 'Payments', eyebrow: 'Finance', icon: Wallet,
    endpoint: '/api/finance/payments', permission: 'view_fees', description: 'Recorded fee payments.',
    columns: [['student_fee.student.user.full_name', 'Student'], ['amount', 'Amount'], ['payment_date', 'Date'], ['payment_method', 'Method'], ['transaction_reference', 'Ref']],
  },
  {
    slug: 'expenses', label: 'Expenses', eyebrow: 'Finance', icon: TrendingDown,
    endpoint: '/api/finance/expenses', permission: 'view_fees', description: 'School operational expenses.',
    columns: [['title', 'Title'], ['category.name', 'Category'], ['amount', 'Amount'], ['expense_date', 'Date'], ['payment_method', 'Method']],
  },
  {
    slug: 'staff-salaries', label: 'Staff Salaries', eyebrow: 'Finance', icon: Banknote,
    endpoint: '/api/finance/salaries', permission: 'view_fees', description: 'Staff and faculty salary payouts.',
    columns: [['user.full_name', 'Staff'], ['amount', 'Amount'], ['payment_date', 'Date'], ['payment_method', 'Method'], ['status', 'Status']],
  },
  {
    slug: 'library', label: 'Library Catalog', eyebrow: 'Operations', icon: Library,
    endpoint: '/api/library/books', permission: 'view_library', description: 'Catalogue availability and lending inventory.',
    columns: [['isbn', 'ISBN'], ['title', 'Title'], ['author', 'Author'], ['category', 'Category'], ['available_copies', 'Available'], ['price', 'Price']],
  },
  {
    slug: 'book-issues', label: 'Issues & Returns', eyebrow: 'Operations', icon: History,
    endpoint: '/api/library/issues', permission: 'view_library', description: 'Active checkouts, overdues and history.',
    columns: [['book_title', 'Book'], ['student_name', 'Student'], ['issue_date', 'Issued On'], ['due_date', 'Due Date'], ['status', 'Status'], ['fine_amount', 'Fine']],
  },
  {
    slug: 'library-categories', label: 'Categories', eyebrow: 'Operations', icon: Tags,
    endpoint: '/api/library/categories', permission: 'view_library', description: 'Book categories and subjects.',
    columns: [['name', 'Name'], ['description', 'Description']],
  },
  {
    slug: 'library-authors', label: 'Authors', eyebrow: 'Operations', icon: PenTool,
    endpoint: '/api/library/authors', permission: 'view_library', description: 'Book authors.',
    columns: [['name', 'Name'], ['bio', 'Bio']],
  },
  {
    slug: 'library-publishers', label: 'Publishers', eyebrow: 'Operations', icon: Printer,
    endpoint: '/api/library/publishers', permission: 'view_library', description: 'Book publishers.',
    columns: [['name', 'Name'], ['contact_email', 'Email']],
  },
  {
    slug: 'library-members', label: 'Members', eyebrow: 'Operations', icon: Users,
    endpoint: '/api/library/members', permission: 'view_library', description: 'Library memberships.',
    columns: [['membership_id', 'Membership ID'], ['user.full_name', 'Member'], ['member_type', 'Type'], ['status', 'Status']],
  },
  {
    slug: 'library-reservations', label: 'Reservations', eyebrow: 'Operations', icon: Bookmark,
    endpoint: '/api/library/reservations', permission: 'view_library', description: 'Book reservations.',
    columns: [['book.title', 'Book'], ['member.user.full_name', 'Member'], ['reservation_date', 'Date'], ['status', 'Status']],
  },
  {
    slug: 'library-fines', label: 'Fines', eyebrow: 'Operations', icon: ReceiptIndianRupee,
    endpoint: '/api/library/fines', permission: 'view_library', description: 'Library fines and payments.',
    columns: [['member.user.full_name', 'Member'], ['amount', 'Amount'], ['reason', 'Reason'], ['is_paid', 'Paid']],
  },
]

export const getValue = (record, path) => path.split('.').reduce((value, key) => value?.[key], record)
