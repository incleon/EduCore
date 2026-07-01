const departments = { endpoint: '/api/departments?page=1&page_size=100', value: 'id', label: 'name' }
const courses = { endpoint: '/api/courses?page=1&page_size=100', value: 'id', label: 'name', filterBy: [{ form: 'department_id', record: 'department_id' }] }
const students = { endpoint: '/api/students?page=1&page_size=100', value: 'id', label: 'user.full_name', fallback: 'enrollment_number' }
const subjects = { endpoint: '/api/subjects?page=1&page_size=100', value: 'id', label: 'name' }
const teachers = { endpoint: '/api/teachers?page=1&page_size=100', value: 'id', label: 'user.full_name', fallback: 'employee_id', filterBy: [{ form: 'department_id', record: 'department_id' }] }
const branches = { endpoint: '/api/academic/branches', value: 'id', label: 'name', filterBy: [{ form: 'course_id', record: 'course_id' }] }
const curricula = { endpoint: '/api/academic/curricula', value: 'id', label: 'name', filterBy: [{ form: 'course_id', record: 'course_id' }, { form: 'branch_id', record: 'branch_id', optional: true }] }
const curriculumVersions = { endpoint: '/api/academic/curriculum-versions', value: 'id', label: 'title', filterBy: [{ form: 'curriculum_id', record: 'curriculum_id' }] }
const academicSemesters = { endpoint: '/api/academic/semesters', value: 'id', label: 'name' }
const sections = { endpoint: '/api/academic/sections', value: 'id', label: 'code', filterBy: [{ form: 'course_id', record: 'course_id' }, { form: 'branch_id', record: 'branch_id', optional: true }] }
const subjectTypes = { endpoint: '/api/academic/subject-types', value: 'id', label: 'name' }
const electiveGroups = { endpoint: '/api/academic/elective-groups', value: 'id', label: 'name' }
const curriculumSubjects = { endpoint: '/api/academic/curriculum-subjects', value: 'id', label: 'subject.name' }
const facultyAssignments = { endpoint: '/api/academic/faculty-assignments', value: 'id', label: 'subject.name', fallback: 'academic_year' }
const feeStructures = { endpoint: '/api/finance/fee-structures?page=1&page_size=100', value: 'id', label: 'name' }
const expenseCategories = { endpoint: '/api/finance/expense-categories?page=1&page_size=100', value: 'id', label: 'name' }
const studentFees = { endpoint: '/api/finance/student-fees?page=1&page_size=100', value: 'id', label: 'title' }
const teacherUsers = { endpoint: '/api/teachers?page=1&page_size=100', value: 'user_id', label: 'user.full_name', fallback: 'employee_id' }
const libraryAuthors = { endpoint: '/api/library/authors', value: 'id', label: 'name' }
const libraryPublishers = { endpoint: '/api/library/publishers', value: 'id', label: 'name' }
const libraryCategories = { endpoint: '/api/library/categories', value: 'id', label: 'name' }

const field = (name, label, type = 'text', extra = {}) => ({ name, label, type, ...extra })

export const resourceForms = {
  students: {
    permission: 'manage_students', noun: 'student',
    create: [
      field('student_id', 'Student ID', 'text', { readOnly: true, disabled: true, placeholder: 'Auto-generated on admission' }),
      field('institutional_email', 'Institutional email', 'email', { readOnly: true, disabled: true, placeholder: 'Auto-generated on admission', wide: true }),
      field('first_name', 'First name', 'text', { required: true }), field('middle_name', 'Middle name'),
      field('last_name', 'Last name', 'text', { required: true }), field('personal_email', 'Personal email', 'email', { required: true, wide: true }),
      field('phone', 'Phone'), field('gender', 'Gender', 'select', { choices: ['male', 'female', 'other'] }),
      field('department_id', 'Department', 'select', { required: true, options: departments }),
      field('course_id', 'Program / course', 'select', { required: true, options: courses }), field('branch_id', 'Branch / specialization', 'select', { options: branches }),
      field('admission_year', 'Admission year', 'number', { required: true, min: 1900, max: 2200 }), field('curriculum_version_id', 'Curriculum version', 'select', { options: curriculumVersions }),
      field('section_id', 'Academic section', 'select', { options: sections }), field('current_semester', 'Current semester', 'number', { required: true, min: 1, max: 20, defaultValue: 1 }),
      field('date_of_birth', 'Date of birth', 'date'), field('admission_date', 'Admission date', 'date'),
      field('guardian_name', 'Guardian name'), field('guardian_phone', 'Guardian phone'),
      field('father_name', 'Father name'), field('mother_name', 'Mother name'), field('blood_group', 'Blood group'),
    ],
    edit: [
      field('full_name', 'Full name', 'text', { source: 'user.full_name', required: true, wide: true }), field('phone', 'Phone', 'text', { source: 'user.phone' }),
      field('department_id', 'Department', 'select', { options: departments }),
      field('course_id', 'Program / course', 'select', { options: courses }), field('branch_id', 'Branch / specialization', 'select', { options: branches }),
      field('admission_year', 'Admission year', 'number', { min: 1900, max: 2200 }), field('curriculum_version_id', 'Curriculum version', 'select', { options: curriculumVersions }),
      field('section_id', 'Academic section', 'select', { options: sections }), field('current_semester', 'Current semester', 'number', { min: 1, max: 20 }),
      field('section', 'Section'), field('guardian_name', 'Guardian name'), field('guardian_phone', 'Guardian phone'),
      field('blood_group', 'Blood group'), field('status', 'Status', 'select', { choices: ['active', 'graduated', 'suspended', 'dropped'] }),
    ],
  },
  teachers: {
    permission: 'manage_teachers', noun: 'faculty member',
    create: [
      field('full_name', 'Full name', 'text', { required: true, wide: true }), 
      field('email', 'Institutional email', 'email', { readOnly: true, disabled: true, placeholder: 'Auto-generated on creation' }),
      field('username', 'Username', 'text', { readOnly: true, disabled: true, placeholder: 'Auto-generated on creation' }),
      field('password', 'Temporary password', 'password', { readOnly: true, disabled: true, placeholder: 'Auto-generated on creation' }),
      field('phone', 'Phone'), field('gender', 'Gender', 'select', { choices: ['male', 'female', 'other'] }),
      field('employee_id', 'Employee ID', 'text', { readOnly: true, disabled: true, placeholder: 'Auto-generated if blank' }), field('department_id', 'Department', 'select', { required: true, options: departments }),
      field('branch_id', 'Branch / specialization', 'select', { options: branches }),
      field('designation', 'Designation', 'select', { choices: ['Professor', 'Assistant Professor', 'Associate Professor'], required: true }), field('specialization', 'Specialization'), field('qualification', 'Qualification'),
      field('joining_date', 'Joining date', 'date'), field('experience_years', 'Experience (years)', 'number', { min: 0, defaultValue: 0 }),
      field('bio', 'Bio', 'textarea', { wide: true }),
    ],
    edit: [
      field('full_name', 'Full name', 'text', { source: 'user.full_name', wide: true }), field('phone', 'Phone', 'text', { source: 'user.phone' }),
      field('department_id', 'Department', 'select', { options: departments }), field('designation', 'Designation', 'select', { choices: ['Professor', 'Assistant Professor', 'Associate Professor'] }),
      field('branch_id', 'Branch / specialization', 'select', { options: branches }),
      field('specialization', 'Specialization'), field('qualification', 'Qualification'),
      field('experience_years', 'Experience (years)', 'number', { min: 0 }), field('bio', 'Bio', 'textarea', { wide: true }),
    ],
  },
  courses: {
    permission: 'manage_departments', noun: 'course',
    create: [field('department_id', 'Department', 'select', { required: true, options: departments }), field('name', 'Program name', 'text', { required: true }), field('code', 'Program code', 'text', { required: true }), field('duration_years', 'Duration (Years)', 'select', { choices: ['1', '2', '3', '4', '5', '6', '7'] }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('department_id', 'Department', 'select', { options: departments }), field('name', 'Program name'), field('code', 'Program code'), field('duration_years', 'Duration (Years)', 'select', { choices: ['1', '2', '3', '4', '5', '6', '7'] }), field('description', 'Description', 'textarea', { wide: true })],
  },
  departments: {
    permission: 'manage_departments', noun: 'department',
    create: [field('name', 'Department name', 'text', { required: true }), field('hod_id', 'Head of department', 'select', { options: teachers }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('name', 'Department name'), field('hod_id', 'Head of department', 'select', { options: teachers }), field('description', 'Description', 'textarea', { wide: true })],
  },
  subjects: {
    permission: 'manage_subjects', noun: 'subject',
    create: [field('name', 'Subject name', 'text', { required: true }), field('code', 'Subject code', 'text', { required: true }), field('subject_type_id', 'Classification', 'select', { required: true, options: subjectTypes }), field('department_id', 'Owning department', 'select', { required: true, options: departments }), field('teacher_id', 'Legacy primary faculty', 'select', { options: teachers }), field('credits', 'Credits', 'number', { min: 0, defaultValue: 3 }), field('type', 'Delivery mode', 'select', { choices: ['theory', 'practical', 'project'], defaultValue: 'theory' }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('name', 'Subject name'), field('code', 'Subject code'), field('subject_type_id', 'Classification', 'select', { options: subjectTypes }), field('department_id', 'Owning department', 'select', { options: departments }), field('teacher_id', 'Legacy primary faculty', 'select', { options: teachers }), field('credits', 'Credits', 'number', { min: 0 }), field('type', 'Delivery mode', 'select', { choices: ['theory', 'practical', 'project'] }), field('description', 'Description', 'textarea', { wide: true })],
  },
  branches: {
    permission: 'manage_academic_structure', noun: 'branch',
    create: [field('course_id', 'Program / course', 'select', { required: true, options: courses }), field('name', 'Branch / specialization name', 'text', { required: true }), field('code', 'Code', 'text', { required: true }), field('hod_id', 'Head of Department', 'select', { options: teachers }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('name', 'Branch / specialization name'), field('code', 'Code'), field('hod_id', 'Head of Department', 'select', { options: teachers }), field('description', 'Description', 'textarea', { wide: true })],
  },
  curricula: {
    permission: 'manage_curriculum', noun: 'curriculum',
    create: [field('course_id', 'Program / course', 'select', { required: true, options: courses }), field('branch_id', 'Branch (optional)', 'select', { options: branches }), field('code', 'Curriculum code', 'text', { required: true }), field('name', 'Curriculum name', 'text', { required: true }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('branch_id', 'Branch (optional)', 'select', { options: branches }), field('name', 'Curriculum name'), field('description', 'Description', 'textarea', { wide: true })],
  },
  'curriculum-versions': {
    permission: 'manage_curriculum', noun: 'curriculum version',
    create: [field('curriculum_id', 'Curriculum', 'select', { required: true, options: curricula }), field('version_code', 'Version code', 'text', { required: true }), field('title', 'Regulation title', 'text', { required: true, wide: true }), field('effective_year', 'Effective year', 'number', { required: true, min: 1900, max: 2200 }), field('applicable_batch_start', 'First applicable batch', 'number', { required: true, min: 1900, max: 2200 }), field('applicable_batch_end', 'Last applicable batch', 'number', { min: 1900, max: 2200 }), field('status', 'Status', 'select', { choices: ['draft', 'active', 'archived'], defaultValue: 'draft' }), field('is_active', 'Published / active', 'boolean', { defaultValue: false })],
    edit: [field('title', 'Regulation title', 'text', { wide: true }), field('effective_year', 'Effective year', 'number', { min: 1900, max: 2200 }), field('applicable_batch_start', 'First applicable batch', 'number', { min: 1900, max: 2200 }), field('applicable_batch_end', 'Last applicable batch', 'number', { min: 1900, max: 2200 }), field('status', 'Status', 'select', { choices: ['draft', 'active', 'archived'] }), field('is_active', 'Published / active', 'boolean')],
  },
  semesters: {
    permission: 'manage_curriculum', noun: 'semester',
    create: [field('curriculum_version_id', 'Curriculum version', 'select', { required: true, options: curriculumVersions }), field('number', 'Semester number', 'number', { required: true, min: 1, max: 20 }), field('name', 'Display name'), field('minimum_credits', 'Minimum credits', 'number', { min: 0, defaultValue: 0 }), field('maximum_credits', 'Maximum credits', 'number', { min: 0 })],
    edit: [field('name', 'Display name'), field('minimum_credits', 'Minimum credits', 'number', { min: 0 }), field('maximum_credits', 'Maximum credits', 'number', { min: 0 })],
  },
  sections: {
    permission: 'manage_academic_structure', noun: 'section',
    create: [field('course_id', 'Program / course', 'select', { required: true, options: courses }), field('branch_id', 'Branch (optional)', 'select', { options: branches }), field('curriculum_version_id', 'Curriculum version', 'select', { options: curriculumVersions }), field('semester_number', 'Semester', 'number', { required: true, min: 1, max: 20 }), field('code', 'Section code', 'text', { required: true }), field('academic_year', 'Academic year', 'text', { required: true }), field('capacity', 'Capacity', 'number', { min: 1 })],
    edit: [field('branch_id', 'Branch (optional)', 'select', { options: branches }), field('curriculum_version_id', 'Curriculum version', 'select', { options: curriculumVersions }), field('code', 'Section code'), field('academic_year', 'Academic year'), field('capacity', 'Capacity', 'number', { min: 1 })],
  },
  'curriculum-subjects': {
    permission: 'manage_curriculum', noun: 'curriculum subject',
    create: [field('semester_id', 'Curriculum semester', 'select', { required: true, options: academicSemesters }), field('subject_id', 'Subject', 'select', { required: true, options: subjects }), field('branch_id', 'Branch scope (blank = common)', 'select', { options: branches }), field('elective_group_id', 'Elective group', 'select', { options: electiveGroups }), field('is_mandatory', 'Mandatory', 'boolean', { defaultValue: true }), field('credits_override', 'Credit override', 'number', { min: 0 }), field('display_order', 'Display order', 'number', { min: 0, defaultValue: 0 })],
    edit: [field('branch_id', 'Branch scope (blank = common)', 'select', { options: branches }), field('elective_group_id', 'Elective group', 'select', { options: electiveGroups }), field('is_mandatory', 'Mandatory', 'boolean'), field('credits_override', 'Credit override', 'number', { min: 0 }), field('display_order', 'Display order', 'number', { min: 0 })],
  },
  'elective-groups': {
    permission: 'manage_curriculum', noun: 'elective group',
    create: [field('semester_id', 'Curriculum semester', 'select', { required: true, options: academicSemesters }), field('code', 'Group code', 'text', { required: true }), field('name', 'Group name', 'text', { required: true }), field('minimum_choices', 'Minimum choices', 'number', { min: 0, defaultValue: 0 }), field('maximum_choices', 'Maximum choices', 'number', { min: 1, defaultValue: 1 }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('name', 'Group name'), field('minimum_choices', 'Minimum choices', 'number', { min: 0 }), field('maximum_choices', 'Maximum choices', 'number', { min: 1 }), field('description', 'Description', 'textarea', { wide: true })],
  },
  'faculty-assignments': {
    permission: 'manage_teachers', noun: 'faculty assignment',
    create: [field('teacher_id', 'Faculty member', 'select', { required: true, options: teachers }), field('curriculum_subject_id', 'Curriculum subject', 'select', { required: true, options: curriculumSubjects }), field('section_id', 'Section (optional)', 'select', { options: sections }), field('academic_year', 'Academic year', 'text', { required: true }), field('role', 'Teaching role', 'select', { choices: ['primary', 'co_faculty', 'lab_instructor'], defaultValue: 'primary' })],
    edit: [field('section_id', 'Section (optional)', 'select', { options: sections }), field('academic_year', 'Academic year'), field('role', 'Teaching role', 'select', { choices: ['primary', 'co_faculty', 'lab_instructor'] })],
  },
  attendance: {
    permission: 'mark_attendance', noun: 'attendance record',
    create: [field('student_id', 'Student', 'select', { required: true, options: students }), field('subject_id', 'Subject', 'select', { required: true, options: subjects }), field('section_id', 'Section', 'select', { options: sections }), field('faculty_assignment_id', 'Teaching allocation', 'select', { options: facultyAssignments }), field('date', 'Date', 'date', { required: true }), field('status', 'Status', 'select', { required: true, choices: ['present', 'absent', 'late', 'excused'], defaultValue: 'present' }), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('section_id', 'Section', 'select', { options: sections }), field('faculty_assignment_id', 'Teaching allocation', 'select', { options: facultyAssignments }), field('status', 'Status', 'select', { choices: ['present', 'absent', 'late', 'excused'] }), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  marks: {
    permission: 'upload_marks', noun: 'marks record',
    create: [field('student_id', 'Student', 'select', { required: true, options: students }), field('subject_id', 'Subject', 'select', { required: true, options: subjects }), field('exam_type', 'Assessment', 'select', { required: true, choices: ['quiz', 'assignment', 'midterm', 'final', 'practical'] }), field('marks_obtained', 'Marks obtained', 'number', { required: true, min: 0, step: '0.01' }), field('max_marks', 'Maximum marks', 'number', { required: true, min: 1, defaultValue: 100, step: '0.01' }), field('semester', 'Semester', 'number', { required: true, min: 1, max: 8 }), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('marks_obtained', 'Marks obtained', 'number', { min: 0, step: '0.01' }), field('max_marks', 'Maximum marks', 'number', { min: 1, step: '0.01' }), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  'fee-structures': {
    permission: 'manage_fees', noun: 'fee structure',
    create: [field('name', 'Structure Name', 'text', { required: true, wide: true }), field('amount', 'Amount', 'number', { required: true, min: 1, step: '0.01' }), field('course_id', 'Course', 'select', { required: true, options: courses }), field('academic_year', 'Academic Year', 'text', { required: true }), field('semester', 'Semester', 'number', { required: true, min: 1, max: 8 }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('name', 'Structure Name', 'text', { wide: true }), field('amount', 'Amount', 'number', { min: 1, step: '0.01' }), field('description', 'Description', 'textarea', { wide: true })],
  },
  'student-fees': {
    permission: 'manage_fees', noun: 'student fee invoice',
    create: [field('student_id', 'Student', 'select', { required: true, options: students }), field('fee_structure_id', 'Fee Structure', 'select', { options: feeStructures }), field('title', 'Invoice Title', 'text', { required: true, wide: true }), field('amount', 'Amount', 'number', { required: true, min: 1, step: '0.01' }), field('due_date', 'Due date', 'date'), field('status', 'Status', 'select', { choices: ['pending', 'partial', 'paid', 'overdue', 'waived'] }), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('title', 'Invoice Title', 'text', { wide: true }), field('amount', 'Amount', 'number', { min: 1, step: '0.01' }), field('due_date', 'Due date', 'date'), field('status', 'Status', 'select', { choices: ['pending', 'partial', 'paid', 'overdue', 'waived'] }), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  payments: {
    permission: 'manage_fees', noun: 'payment record',
    create: [field('student_fee_id', 'Invoice', 'select', { required: true, options: studentFees, wide: true }), field('amount', 'Amount', 'number', { required: true, min: 1, step: '0.01' }), field('payment_date', 'Payment Date', 'date', { required: true }), field('payment_method', 'Payment Method', 'select', { required: true, choices: ['cash', 'cheque', 'bank_transfer', 'upi', 'online'] }), field('transaction_reference', 'Transaction Ref', 'text'), field('status', 'Status', 'select', { choices: ['success', 'pending', 'failed', 'refunded'], defaultValue: 'success' }), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('amount', 'Amount', 'number', { min: 1, step: '0.01' }), field('payment_date', 'Payment Date', 'date'), field('payment_method', 'Payment Method', 'select', { choices: ['cash', 'cheque', 'bank_transfer', 'upi', 'online'] }), field('transaction_reference', 'Transaction Ref', 'text'), field('status', 'Status', 'select', { choices: ['success', 'pending', 'failed', 'refunded'] }), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  expenses: {
    permission: 'manage_fees', noun: 'expense',
    create: [field('title', 'Expense Title', 'text', { required: true, wide: true }), field('category_id', 'Category', 'select', { required: true, options: expenseCategories }), field('amount', 'Amount', 'number', { required: true, min: 1, step: '0.01' }), field('expense_date', 'Expense Date', 'date', { required: true }), field('receipt_url', 'Receipt URL', 'text'), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('title', 'Expense Title', 'text', { wide: true }), field('category_id', 'Category', 'select', { options: expenseCategories }), field('amount', 'Amount', 'number', { min: 1, step: '0.01' }), field('expense_date', 'Expense Date', 'date'), field('receipt_url', 'Receipt URL', 'text'), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  'staff-salaries': {
    permission: 'manage_fees', noun: 'salary payout',
    create: [field('user_id', 'Staff Member', 'select', { required: true, options: teacherUsers }), field('amount', 'Amount', 'number', { required: true, min: 1, step: '0.01' }), field('payment_date', 'Payment Date', 'date', { required: true }), field('month', 'Salary Month', 'number', { required: true, min: 1, max: 12 }), field('year', 'Salary Year', 'number', { required: true, min: 2001 }), field('payment_method', 'Payment Method', 'select', { required: true, choices: ['cash', 'cheque', 'bank_transfer', 'upi', 'online'] }), field('transaction_reference', 'Transaction Ref', 'text'), field('remarks', 'Remarks', 'textarea', { wide: true })],
    edit: [field('amount', 'Amount', 'number', { min: 1, step: '0.01' }), field('payment_date', 'Payment Date', 'date'), field('month', 'Salary Month', 'number', { min: 1, max: 12 }), field('year', 'Salary Year', 'number', { min: 2001 }), field('payment_method', 'Payment Method', 'select', { choices: ['cash', 'cheque', 'bank_transfer', 'upi', 'online'] }), field('transaction_reference', 'Transaction Ref', 'text'), field('remarks', 'Remarks', 'textarea', { wide: true })],
  },
  library: {
    permission: 'manage_library', noun: 'book',
    create: [field('title', 'Book title', 'text', { required: true, wide: true }), field('author_id', 'Author', 'select', { required: true, options: libraryAuthors }), field('isbn', 'ISBN'), field('publisher_id', 'Publisher', 'select', { options: libraryPublishers }), field('edition', 'Edition'), field('category_id', 'Category', 'select', { options: libraryCategories }), field('total_copies', 'Total copies', 'number', { required: true, min: 1, defaultValue: 1 }), field('shelf_location', 'Shelf location'), field('price', 'Price', 'number', { min: 0, step: '0.01' }), field('description', 'Description', 'textarea', { wide: true })],
    edit: [field('title', 'Book title', 'text', { wide: true }), field('author_id', 'Author', 'select', { options: libraryAuthors }), field('isbn', 'ISBN'), field('publisher_id', 'Publisher', 'select', { options: libraryPublishers }), field('category_id', 'Category', 'select', { options: libraryCategories }), field('total_copies', 'Total copies', 'number', { min: 1 }), field('shelf_location', 'Shelf location'), field('price', 'Price', 'number', { min: 0, step: '0.01' }), field('description', 'Description', 'textarea', { wide: true })],
  },
}
