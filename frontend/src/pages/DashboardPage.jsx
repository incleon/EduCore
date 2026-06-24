import { useEffect, useMemo, useState } from 'react'
import { Activity, BookOpen, Building2, CalendarDays, CircleDollarSign, GraduationCap, LoaderCircle, Sparkles, UsersRound } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../lib/api'
import { useAuth } from '../state/AuthContext'
import PageHeader from '../components/ui/PageHeader'
import StatCard from '../components/ui/StatCard'

const icons = [GraduationCap, UsersRound, Building2, BookOpen, CircleDollarSign]
const tones = ['violet', 'mint', 'amber', 'blue', 'rose']

export default function DashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { api.get('/api/dashboard').then(setDashboard).catch((err) => setError(err.message)) }, [])

  const data = useMemo(() => dashboard?.data || {}, [dashboard])
  const chartData = useMemo(() => (data.trend_labels || []).map((month, index) => ({
    month, enrollments: data.trend_enrollments?.[index] || 0, revenue: data.trend_revenue?.[index] || 0,
  })), [data])
  const firstName = user.full_name?.split(' ')[0] || 'there'

  if (!dashboard && !error) return <div className="content-loader"><LoaderCircle className="spin" /><span>Loading your overview</span></div>

  return <>
    <PageHeader eyebrow="WORKSPACE OVERVIEW" title={`Good morning, ${firstName}.`} description="Here’s what is happening across your campus today." actions={<div className="date-pill"><CalendarDays size={16} /> June 24, 2026</div>} />
    {error && <div className="inline-error">{error}</div>}

    <section className="stats-grid">
      {(data.stats || []).slice(0, 5).map((stat, index) => <StatCard key={stat.label} label={stat.label} value={stat.value} icon={icons[index % icons.length]} tone={tones[index % tones.length]} />)}
    </section>

    <section className="dashboard-grid">
      <article className="panel trend-panel">
        <div className="panel-heading"><div><p className="eyebrow">CAMPUS MOMENTUM</p><h2>Enrollment trend</h2></div><span className="quiet-chip">Last 6 months</span></div>
        {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 8, left: -28, bottom: 0 }}><defs><linearGradient id="navyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#003049" stopOpacity={0.24}/><stop offset="100%" stopColor="#003049" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(0,48,73,.1)" /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><Tooltip contentStyle={{ border: 0, borderRadius: 12, boxShadow: '0 12px 32px rgba(0,48,73,.12)' }} /><Area type="monotone" dataKey="enrollments" stroke="#003049" strokeWidth={2.5} fill="url(#navyFade)" /></AreaChart></ResponsiveContainer></div> : <EmptyChart />}
      </article>

      <article className="panel activity-panel">
        <div className="panel-heading"><div><p className="eyebrow">LIVE FEED</p><h2>Recent activity</h2></div><Activity size={18} className="muted-icon" /></div>
        <div className="activity-list">{(data.recent_activities || []).slice(0, 5).map((item, index) => <div className="activity-row" key={`${item.time}-${index}`}><span className="activity-marker" style={{ background: item.color }} /><div><p dangerouslySetInnerHTML={{ __html: item.text }} /><small>{item.time}</small></div></div>)}{!data.recent_activities?.length && <div className="soft-empty"><Sparkles size={22} /><p>Your campus activity will appear here.</p></div>}</div>
      </article>
    </section>

    <section className="panel insight-strip"><span className="insight-icon"><Sparkles size={19} /></span><div><strong>Everything looks steady.</strong><p>Your operational data is synced and the campus workspace is ready.</p></div><span className="health-badge"><i /> Healthy</span></section>
  </>
}

function EmptyChart() {
  return <div className="empty-chart"><div className="chart-skeleton"><i /><i /><i /><i /><i /><i /></div><p>Trend data will build as new records are added.</p></div>
}
