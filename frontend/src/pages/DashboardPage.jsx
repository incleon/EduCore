import { useEffect, useMemo, useState } from 'react'
import { Activity, BookOpen, Building2, CalendarCheck2, CalendarDays, CircleDollarSign, GitBranch, GraduationCap, Hash, Layers3, LoaderCircle, ScrollText, Shapes, Sparkles, UsersRound, AlertTriangle, Clock, ListChecks, ArrowRight, UserX, BarChart2, BookMarked, Wallet } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'
import { api } from '../lib/api'
import { useAuth } from '../state/AuthContext'
import PageHeader from '../components/ui/PageHeader'
import StatCard from '../components/ui/StatCard'

import '../styles/dashboard-widgets.css'

const icons = [GraduationCap, UsersRound, Building2, BookOpen, CircleDollarSign]
const tones = ['violet', 'mint', 'amber', 'blue', 'rose']
const PIE_COLORS = ['#003049', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function DashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { api.get('/api/dashboard').then(setDashboard).catch((err) => setError(err.message)) }, [])

  const data = useMemo(() => dashboard?.data || {}, [dashboard])
  const role = dashboard?.role
  const isStudent = role === 'student'
  const isLibrarian = role === 'librarian'
  const isAccountant = role === 'accountant'
  const isAdmin = role === 'admin'
  const isTeacher = role === 'teacher'
  const isHod = role === 'hod'

  const firstName = user.full_name?.split(' ')[0] || 'there'

  if (!dashboard && !error) return <div className="content-loader"><LoaderCircle className="spin" /><span>Loading your overview</span></div>

  return <>
    <PageHeader 
      eyebrow={isStudent ? 'MY OVERVIEW' : isLibrarian ? 'LIBRARY DESK' : isAccountant ? 'FINANCE DESK' : 'WORKSPACE OVERVIEW'} 
      title={`Good ${getGreeting()}, ${firstName}.`} 
      description={isStudent ? 'Here\'s your academic snapshot and enrollment details.' : isLibrarian ? 'Here\'s the latest on the library catalog and issues.' : isAccountant ? 'Here is the current financial standing.' : 'Here\'s what is happening across your campus today.'} 
      actions={<div className="date-pill"><CalendarDays size={16} /> {formatDate()}</div>} 
    />
    {error && <div className="inline-error">{error}</div>}

    {isAdmin && data.system_alerts?.length > 0 && (
      <section className="panel" style={{ background: '#fef2f2', border: '1px solid #fecaca', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626', fontWeight: 600, marginBottom: '12px' }}>
          <AlertTriangle size={20} /> Action Required
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {data.system_alerts.map((alert, i) => (
            <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '14px', color: '#991b1b' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#dc2626' }}></span>
              {alert.message}
            </div>
          ))}
        </div>
      </section>
    )}

    <section className="stats-grid">
      {(data.stats || []).slice(0, 5).map((stat, index) => <StatCard key={stat.label} label={stat.label} value={stat.value} icon={icons[index % icons.length]} tone={tones[index % tones.length]} />)}
    </section>

    {isStudent && data.enrollment && Object.keys(data.enrollment).length > 0 && <EnrollmentCard enrollment={data.enrollment} />}

    <section className="dashboard-grid">
      {/* ── ROLE SPECIFIC WIDGETS ── */}
      {isAdmin && <AdminPanels data={data} />}
      {isTeacher && <TeacherPanels data={data} />}
      {isStudent && <StudentPanels data={data} />}
      {isHod && <HodPanels data={data} />}
      {isAccountant && <AccountantPanels data={data} />}
      {isLibrarian && <LibrarianPanels data={data} />}
    </section>
  </>
}

function AdminPanels({ data }) {
  const chartData = useMemo(() => (data.trend_labels || []).map((month, index) => ({
    month, 
    enrollments: data.trend_enrollments?.[index] || 0, 
    revenue: data.trend_revenue?.[index] || 0,
  })), [data])

  return (
    <>
      <article className="panel trend-panel" style={{ gridColumn: 'span 2' }}>
        <div className="panel-heading"><div><p className="eyebrow">CAMPUS MOMENTUM</p><h2>Enrollment Trend</h2></div><span className="quiet-chip">Last 6 months</span></div>
        {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 8, left: -28, bottom: 0 }}><defs><linearGradient id="navyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#003049" stopOpacity={0.24}/><stop offset="100%" stopColor="#003049" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(0,48,73,.1)" /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><Tooltip contentStyle={{ border: 0, borderRadius: 12, boxShadow: '0 12px 32px rgba(0,48,73,.12)' }} />
            <Area type="monotone" dataKey="enrollments" stroke="#003049" strokeWidth={2.5} fill="url(#navyFade)" />
        </AreaChart></ResponsiveContainer></div> : <EmptyChart />}
      </article>

      <article className="panel activity-panel">
        <div className="panel-heading"><div><p className="eyebrow">LIVE FEED</p><h2>Recent Activity</h2></div><Activity size={18} className="muted-icon" /></div>
        <div className="activity-list">{(data.recent_activities || []).slice(0, 5).map((item, index) => <div className="activity-row" key={`${item.time}-${index}`}><span className="activity-marker" style={{ background: item.color }} /><div><p dangerouslySetInnerHTML={{ __html: item.text }} /><small>{item.time}</small></div></div>)}{!data.recent_activities?.length && <div className="soft-empty"><Sparkles size={22} /><p>Your campus activity will appear here.</p></div>}</div>
      </article>
    </>
  )
}

function TeacherPanels({ data }) {
  return (
    <>
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">SCHEDULE</p><h2>Week at a Glance</h2></div></div>
        <div className="generic-list">
          {data.week_at_a_glance?.map((s, i) => (
            <div key={i} className="list-item">
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div style={{ padding: '8px', background: '#f1f5f9', borderRadius: '8px', color: '#475569' }}><Clock size={20} /></div>
                <div><strong>{s.subject}</strong><div style={{ fontSize: '13px', color: '#64748b' }}>{s.time} • {s.room}</div></div>
              </div>
            </div>
          ))}
          {!data.week_at_a_glance?.length && <p className="soft-empty">No schedule available.</p>}
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">ATTENTION REQUIRED</p><h2>At-Risk Students</h2></div></div>
        <div className="generic-list">
          {data.at_risk_students?.map((s, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#fee2e2', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><UserX size={18} /></div>
                <div><strong>{s.name}</strong><div style={{ fontSize: '13px', color: '#ef4444' }}>{s.reason}</div></div>
              </div>
              <button className="btn-sm" style={{ padding: '6px 12px', border: '1px solid #e2e8f0', borderRadius: '6px', background: 'white', cursor: 'pointer' }}>Message</button>
            </div>
          ))}
          {!data.at_risk_students?.length && <p className="soft-empty">No students at risk.</p>}
        </div>
      </article>
    </>
  )
}

function StudentPanels({ data }) {
  return (
    <>
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">UPCOMING</p><h2>Deadline Tracker</h2></div></div>
        <div className="generic-list">
          {data.deadline_tracker?.map((t, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div style={{ padding: '8px', background: '#f1f5f9', borderRadius: '8px', color: '#475569' }}><ListChecks size={20} /></div>
                <div><strong>{t.task}</strong><div style={{ fontSize: '13px', color: '#64748b' }}>Due: {t.date}</div></div>
              </div>
              <span style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '20px', background: t.urgency === 'high' ? '#fee2e2' : '#fef3c7', color: t.urgency === 'high' ? '#ef4444' : '#d97706', fontWeight: 600 }}>{t.urgency.toUpperCase()}</span>
            </div>
          ))}
          {!data.deadline_tracker?.length && <p className="soft-empty">No upcoming deadlines.</p>}
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">TODAY</p><h2>Real-time Schedule</h2></div></div>
        <div className="generic-list">
          {data.real_time_schedule?.map((s, i) => (
            <div key={i} className="list-item">
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div style={{ padding: '8px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#0f172a', fontWeight: 600, fontSize: '14px' }}>{s.time}</div>
                <div><strong>{s.subject}</strong><div style={{ fontSize: '13px', color: '#64748b' }}>{s.room}</div></div>
              </div>
            </div>
          ))}
          {!data.real_time_schedule?.length && <p className="soft-empty">No classes today.</p>}
        </div>
      </article>
    </>
  )
}

function HodPanels({ data }) {
  return (
    <>
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">ACADEMICS</p><h2>At-Risk Subjects</h2></div></div>
        <div className="generic-list">
          {data.at_risk_subjects?.map((s, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between' }}>
              <div><strong>{s.name}</strong><div style={{ fontSize: '13px', color: '#ef4444' }}>{s.issue}</div></div>
              <button className="btn-sm" style={{ padding: '6px 12px', border: '1px solid #e2e8f0', borderRadius: '6px', background: 'white', cursor: 'pointer' }}>Review</button>
            </div>
          ))}
          {!data.at_risk_subjects?.length && <p className="soft-empty">No at-risk subjects.</p>}
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">RESOURCES</p><h2>Workload Distribution</h2></div></div>
        <div className="chart-wrap" style={{ height: '220px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.workload_distribution || []} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="teacher" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="hours" name="Hours/Week" fill="#003049" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>
    </>
  )
}

function AccountantPanels({ data }) {
  return (
    <>
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">COLLECTIONS</p><h2>High-Risk Defaulters</h2></div></div>
        <div className="generic-list">
          {data.high_risk_defaulters?.map((d, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #f1f5f9', border: 'none', background: 'transparent' }}>
              <div><strong>{d.name}</strong><div style={{ fontSize: '13px', color: '#ef4444' }}>{d.days_overdue} days overdue</div></div>
              <div style={{ textAlign: 'right' }}>
                <strong style={{ display: 'block' }}>₹{d.amount.toLocaleString()}</strong>
                <button className="btn-sm" style={{ padding: '4px 8px', fontSize: '12px', border: 'none', color: '#2563eb', background: 'none', cursor: 'pointer', marginTop: '2px' }}>Send Notice</button>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">REVENUE</p><h2>Revenue Breakdown</h2></div></div>
        <div className="chart-wrap" style={{ height: '220px', display: 'flex', alignItems: 'center' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data.revenue_breakdown || []} dataKey="amount" nameKey="category" cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={2}>
                {(data.revenue_breakdown || []).map((entry, index) => <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ minWidth: '120px' }}>
            {(data.revenue_breakdown || []).map((entry, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '13px', color: '#475569' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: PIE_COLORS[index % PIE_COLORS.length] }}></span>
                {entry.category}
              </div>
            ))}
          </div>
        </div>
      </article>
    </>
  )
}

function LibrarianPanels({ data }) {
  const chartData = useMemo(() => (data.trend_labels || []).map((month, index) => ({
    month, 
    issues: data.trend_issues?.[index] || 0,
    returns: data.trend_returns?.[index] || 0,
  })), [data])

  return (
    <>
      <article className="panel trend-panel" style={{ gridColumn: 'span 2' }}>
        <div className="panel-heading"><div><p className="eyebrow">LIBRARY MOMENTUM</p><h2>Issues & Returns</h2></div><span className="quiet-chip">Last 6 months</span></div>
        {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 8, left: -28, bottom: 0 }}><defs><linearGradient id="navyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#003049" stopOpacity={0.24}/><stop offset="100%" stopColor="#003049" stopOpacity={0}/></linearGradient><linearGradient id="mintFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10b981" stopOpacity={0.24}/><stop offset="100%" stopColor="#10b981" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(0,48,73,.1)" /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#61737a', fontSize: 12 }} /><Tooltip contentStyle={{ border: 0, borderRadius: 12, boxShadow: '0 12px 32px rgba(0,48,73,.12)' }} />
              <Area type="monotone" dataKey="issues" name="Issues" stroke="#003049" strokeWidth={2.5} fill="url(#navyFade)" />
              <Area type="monotone" dataKey="returns" name="Returns" stroke="#10b981" strokeWidth={2.5} fill="url(#mintFade)" />
        </AreaChart></ResponsiveContainer></div> : <EmptyChart />}
      </article>
      
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">INVENTORY</p><h2>Low Stock Alerts</h2></div></div>
        <div className="generic-list">
          {data.low_stock_alerts?.map((b, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between' }}>
              <div><strong>{b.title}</strong><div style={{ fontSize: '13px', color: '#f59e0b' }}>{b.requests} active requests</div></div>
              <span style={{ padding: '4px 10px', background: '#fef3c7', color: '#d97706', borderRadius: '12px', fontSize: '13px', fontWeight: 600 }}>{b.available} left</span>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">CIRCULATION</p><h2>Overdue Actions</h2></div></div>
        <div className="generic-list">
          {data.overdue_actions?.map((a, i) => (
            <div key={i} className="list-item" style={{ justifyContent: 'space-between' }}>
              <div><strong>{a.student}</strong><div style={{ fontSize: '13px', color: '#ef4444' }}>{a.book} ({a.days_overdue} days late)</div></div>
              <button className="btn-sm" style={{ padding: '6px 12px', border: '1px solid #e2e8f0', borderRadius: '6px', background: 'white', cursor: 'pointer' }}>Notice</button>
            </div>
          ))}
        </div>
      </article>
    </>
  )
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}

function formatDate() {
  return new Date().toLocaleDateString('en-IN', { month: 'long', day: 'numeric', year: 'numeric' })
}

function EnrollmentCard({ enrollment }) {
  const fields = [
    { label: 'Student ID', value: enrollment.student_id, icon: Hash },
    { label: 'Department', value: enrollment.department, icon: Building2 },
    { label: 'Course', value: enrollment.course, icon: BookOpen },
    { label: 'Branch', value: enrollment.branch, icon: GitBranch },
    { label: 'Curriculum', value: enrollment.curriculum_version, icon: Layers3 },
    { label: 'Semester', value: enrollment.current_semester, icon: CalendarCheck2 },
    { label: 'Section', value: enrollment.section, icon: Shapes },
    { label: 'Admission Year', value: enrollment.admission_year, icon: ScrollText },
  ].filter((f) => f.value != null)

  const statusColor = enrollment.status === 'active' ? '#38a169' : '#e53e3e'

  return (
    <section className="enrollment-card">
      <div className="enrollment-header">
        <div>
          <p className="eyebrow">MY ENROLLMENT</p>
          <h2>Academic Profile</h2>
        </div>
        {enrollment.status && (
          <span className="enrollment-status" style={{ '--status-color': statusColor }}>
            <i />{enrollment.status.charAt(0).toUpperCase() + enrollment.status.slice(1)}
          </span>
        )}
      </div>
      <div className="enrollment-grid">
        {fields.map(({ label, value, icon: Icon }) => (
          <div className="enrollment-field" key={label}>
            <div className="enrollment-field-icon"><Icon size={16} strokeWidth={2} /></div>
            <div>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function EmptyChart() {
  return <div className="empty-chart"><div className="chart-skeleton"><i /><i /><i /><i /><i /><i /></div><p>Trend data will build as new records are added.</p></div>
}
