import { ArrowUpRight } from 'lucide-react'

export default function StatCard({ label, value, icon: Icon, tone = 'violet', note }) {
  return <article className="stat-card">
    <div className={`stat-icon ${tone}`}><Icon size={20} /></div>
    <div className="stat-copy"><span>{label}</span><strong>{value ?? '—'}</strong></div>
    {note && <small><ArrowUpRight size={13} />{note}</small>}
  </article>
}
