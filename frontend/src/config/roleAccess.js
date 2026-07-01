const STUDENT_RESOURCES = new Set([
  'attendance',
  'marks',
  'student-fees',
  'payments',
  'library',
  'book-issues',
  'library-reservations',
  'library-fines',
])

const TEACHER_RESOURCES = new Set([
  'students',
  'subjects',
  'faculty-assignments',
  'attendance',
  'marks',
  'library',
  'book-issues',
  'library-reservations',
  'library-fines',
])

const STUDENT_LABELS = {
  attendance: 'My Attendance',
  marks: 'My Marks',
  'student-fees': 'My Fees',
  payments: 'My Payments',
  'book-issues': 'My Issues',
  'library-reservations': 'My Reservations',
  'library-fines': 'My Fines',
}

const TEACHER_LABELS = {
  students: 'My Students',
  subjects: 'My Subjects',
  'faculty-assignments': 'My Teaching Assignments',
  attendance: 'Student Attendance',
  marks: 'Student Marks',
  'book-issues': 'My Issues',
  'library-reservations': 'My Reservations',
  'library-fines': 'My Fines',
}

export const isStudentWorkspace = (user) =>
  user?.roles?.includes('student') && !user?.roles?.includes('admin')

export const isTeacherWorkspace = (user) =>
  user?.roles?.includes('teacher') &&
  !user?.roles?.includes('admin') &&
  !user?.roles?.includes('hod') &&
  !user?.is_hod

export function canAccessResourceForRole(user, slug) {
  if (isStudentWorkspace(user)) return STUDENT_RESOURCES.has(slug)
  if (isTeacherWorkspace(user)) return TEACHER_RESOURCES.has(slug)
  return true
}

export function resourceLabelForRole(user, resource) {
  if (isStudentWorkspace(user)) return STUDENT_LABELS[resource.slug] || resource.label
  if (isTeacherWorkspace(user)) return TEACHER_LABELS[resource.slug] || resource.label
  return resource.label
}

export function canAccessAssignments(user) {
  return Boolean(
    user?.roles?.some((role) => ['admin', 'hod', 'teacher', 'student'].includes(role)) ||
    user?.is_hod
  )
}

export function canAccessTimetable(user) {
  return canAccessAssignments(user)
}
