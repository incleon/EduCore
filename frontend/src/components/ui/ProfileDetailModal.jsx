import { LoaderCircle, Mail, Phone, UserRound, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../lib/api'

const hidden = new Set(['id', 'user_id', 'department_id', 'course_id', 'branch_id', 'curriculum_version_id', 'section_id', 'profile_image'])
const humanize = (value) => String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
const show = (value) => value === null || value === undefined || value === '' ? '—' : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : humanize(value)

export default function ProfileDetailModal({ endpoint, record, kind, onClose }) {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { api.get(`${endpoint}/${record.id}`).then(setProfile).catch((err) => setError(err.message)) }, [endpoint, record.id])
  const details = useMemo(() => profile ? Object.entries(profile).filter(([key, value]) => !hidden.has(key) && typeof value !== 'object') : [], [profile])
  const name = profile?.full_name || record.user?.full_name || 'Profile'
  return <div className="modal-backdrop modern" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className="profile-detail-modal" role="dialog" aria-modal="true">
      <header><div className="profile-detail-avatar">{name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</div><div><p>{kind === 'students' ? 'STUDENT PROFILE' : 'FACULTY PROFILE'}</p><h2>{name}</h2><span>{profile?.student_id || profile?.faculty_id || profile?.employee_id}</span></div><button onClick={onClose} aria-label="Close profile"><X size={20} /></button></header>
      {!profile && !error && <div className="profile-loading"><LoaderCircle className="spin" /> Loading complete profile</div>}
      {error && <div className="inline-error">{error}</div>}
      {profile && <><div className="profile-contact">{profile.email && <span><Mail size={15}/>{profile.email}</span>}{profile.phone && <span><Phone size={15}/>{profile.phone}</span>}<span><UserRound size={15}/>{profile.department_name || 'Institution account'}</span></div><div className="profile-detail-grid">{details.map(([key, value]) => <div key={key}><span>{humanize(key)}</span><strong>{show(value)}</strong></div>)}</div></>}
    </section>
  </div>
}
