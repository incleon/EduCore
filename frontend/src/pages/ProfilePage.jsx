import { useEffect, useState } from 'react'
import { KeyRound, LoaderCircle, Mail, ShieldCheck, UserRound } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import { useAuth } from '../state/AuthContext'
import { api } from '../lib/api'

const label = (value) => String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
const value = (item) => item === null || item === undefined || item === '' ? '—' : label(item)

function ProfileSection({ title, data }) {
  if (!data) return null
  return <article className="panel details-card"><h2>{title}</h2>{Object.entries(data).filter(([key]) => key !== 'id' && key !== 'bio').map(([key, item]) => <div className="detail-row" key={key}><UserRound size={18}/><div><span>{label(key)}</span><strong>{value(item)}</strong></div></div>)}{data.bio && <div className="detail-row"><UserRound size={18}/><div><span>Bio</span><strong>{data.bio}</strong></div></div>}</article>
}

export default function ProfilePage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { api.get('/auth/profile').then(setProfile).catch((err) => setError(err.message)) }, [])
  const account = profile || user
  return <>
    <PageHeader eyebrow="ACCOUNT" title="Your profile" description="Your complete identity, role and institutional record." />
    {error && <div className="inline-error">{error}</div>}
    {!profile && !error ? <div className="table-state"><LoaderCircle className="spin"/> Loading profile</div> : <section className="profile-grid">
      <article className="panel identity-card"><div className="profile-avatar">{account.full_name?.split(' ').map((part) => part[0]).slice(0, 2).join('')}</div><h2>{account.full_name}</h2><p>{account.roles?.map((role) => role.toUpperCase()).join(' · ')}</p></article>
      <article className="panel details-card"><h2>Account details</h2><div className="detail-row"><Mail size={18}/><div><span>Email</span><strong>{account.email}</strong></div></div><div className="detail-row"><UserRound size={18}/><div><span>Username</span><strong>{account.username || `#${account.id}`}</strong></div></div><div className="detail-row"><ShieldCheck size={18}/><div><span>Permissions</span><strong>{account.permissions?.length || 0} assigned</strong></div></div><div className="detail-row"><KeyRound size={18}/><div><span>Authentication</span><strong>Secure cookie session</strong></div></div></article>
      <ProfileSection title="Student details" data={profile.student}/><ProfileSection title="Faculty details" data={profile.teacher}/>
    </section>}
  </>
}
