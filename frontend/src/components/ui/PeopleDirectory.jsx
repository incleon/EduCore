import { BookOpen, Building2, Eye, GitBranch, GraduationCap, Mail, Pencil, Trash2, UserRound } from 'lucide-react'

const initials = (name = '') => name
  .split(' ')
  .filter(Boolean)
  .map((part) => part.replace('.', '')[0])
  .filter(Boolean)
  .slice(0, 2)
  .join('')
  .toUpperCase()

const readable = (value, fallback = 'Not assigned') => value || fallback

export default function PeopleDirectory({
  kind,
  records,
  loading,
  emptyIcon: EmptyIcon,
  canManage,
  onView,
  onEdit,
  onDelete,
}) {
  const isStudent = kind === 'students'

  if (loading) {
    return <div className="people-directory-state"><span className="people-directory-loader" /><strong>Preparing the directory</strong><p>Loading profiles and academic details…</p></div>
  }

  if (!records.length) {
    return <div className="people-directory-state"><EmptyIcon size={26} /><strong>No people found</strong><p>Try adjusting the filters or search terms.</p></div>
  }

  return (
    <div className="people-directory">
      <div className="people-directory__intro">
        <div>
          <p className="eyebrow">{isStudent ? 'STUDENT DIRECTORY' : 'FACULTY DIRECTORY'}</p>
          <strong>{isStudent ? 'Enrolled learner profiles' : 'Academic staff profiles'}</strong>
        </div>
        <span>{records.length} shown on this page</span>
      </div>

      <div className="people-directory__grid">
        {records.map((record, index) => {
          const name = readable(record.user?.full_name, isStudent ? 'Unnamed student' : 'Unnamed faculty member')
          const identifier = isStudent ? record.student_id : record.faculty_id
          const course = isStudent ? record.course?.name : record.branch?.course?.name
          const branch = record.branch?.name
          const status = isStudent ? (record.status?.value || record.status || 'active') : record.designation
          const tone = (record.id ?? index) % 5

          return (
            <article className="person-card" key={record.id ?? identifier}>
              <header className="person-card__header">
                <div className={`person-card__avatar tone-${tone}`}>{initials(name)}</div>
                <div className="person-card__identity">
                  <h3>{name}</h3>
                  <span className="person-card__identifier">{identifier || record.employee_id || 'ID pending'}</span>
                </div>
                <span className={`person-card__badge ${isStudent ? String(status).toLowerCase() : 'faculty'}`}>
                  {String(status).replaceAll('_', ' ')}
                </span>
              </header>

              <div className="person-card__email"><Mail size={14} /><span>{readable(record.user?.email, 'Institutional email unavailable')}</span></div>

              <dl className="person-card__details">
                <div>
                  <dt><Building2 size={14} /> Department</dt>
                  <dd>{readable(record.department?.name)}</dd>
                </div>
                <div>
                  <dt><BookOpen size={14} /> Programme</dt>
                  <dd>{readable(course)}</dd>
                </div>
                <div>
                  <dt><GitBranch size={14} /> Branch</dt>
                  <dd>{readable(branch)}</dd>
                </div>
                <div>
                  <dt>{isStudent ? <GraduationCap size={14} /> : <UserRound size={14} />} {isStudent ? 'Class' : 'Role'}</dt>
                  <dd>{isStudent ? `Semester ${record.semester || record.current_semester || '—'} · Section ${record.section || '—'}` : readable(record.specialization, record.designation)}</dd>
                </div>
              </dl>

              <footer className="person-card__footer">
                <button className="person-card__view" onClick={() => onView(record)}>
                  <Eye size={15} /> View full profile
                </button>
                {canManage && (
                  <div className="person-card__actions">
                    <button onClick={() => onEdit(record)} aria-label={`Edit ${name}`} title="Edit profile"><Pencil size={15} /></button>
                    <button className="delete" onClick={() => onDelete(record)} aria-label={`Delete ${name}`} title="Delete profile"><Trash2 size={15} /></button>
                  </div>
                )}
              </footer>
            </article>
          )
        })}
      </div>
    </div>
  )
}
