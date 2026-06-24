import { Bell, CheckCheck, LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import PageHeader from '../components/ui/PageHeader'
import { api } from '../lib/api'

export default function NotificationsPage() {
  const [data, setData] = useState({ items: [], unread: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = () => api.get('/api/notifications').then(setData).catch((err) => setError(err.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const markAll = async () => { await api.post('/api/notifications/mark-all-read', {}); await load() }

  return <>
    <PageHeader eyebrow="INBOX" title="Notifications" description="Updates and actions from across your campus." actions={data.unread > 0 && <button className="secondary-button" onClick={markAll}><CheckCheck size={16} /> Mark all read</button>} />
    <section className="panel notifications-panel">
      {loading ? <div className="table-state"><LoaderCircle className="spin" /> Loading notifications</div>
        : error ? <div className="table-state error">{error}</div>
        : data.items.length ? data.items.map((item) => <article className={`notification-row ${item.is_read ? '' : 'unread'}`} key={item.id}><span className={`notification-type ${item.notification_type}`}><Bell size={16} /></span><div><div><h2>{item.title}</h2>{!item.is_read && <i />}</div><p>{item.message}</p><small>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Recently'}</small></div></article>)
        : <div className="table-state"><Bell size={24} /><strong>You’re all caught up</strong><span>New campus updates will appear here.</span></div>}
    </section>
  </>
}
