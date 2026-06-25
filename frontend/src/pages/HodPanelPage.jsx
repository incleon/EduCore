import { useState } from 'react'
import { CalendarRange, GraduationCap, UsersRound, BookOpen } from 'lucide-react'
import { useAuth } from '../state/AuthContext'
import PageHeader from '../components/ui/PageHeader'
import ResourcePage from './ResourcePage'
import { resourceConfigs } from '../config/resources'
import TimetablePage from './TimetablePage'

export default function HodPanelPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('students')
  
  const branchId = user?.hod_branch_ids?.[0]
  if (!branchId) return <div className="inline-error">You are not assigned as HOD of any branch.</div>

  const tabs = [
    { id: 'students', label: 'Students', icon: GraduationCap },
    { id: 'teachers', label: 'Teachers', icon: UsersRound },
    { id: 'subjects', label: 'Subjects', icon: BookOpen },
    { id: 'timetable', label: 'Timetable', icon: CalendarRange },
  ]

  const getConfig = (slug) => resourceConfigs.find(c => c.slug === slug)

  return (
    <>
      <PageHeader eyebrow="HEAD OF DEPARTMENT" title="Branch Administration" description="Manage students, faculty, and academic schedule for your branch." />
      
      <div className="tabs-row" style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: '24px' }}>
        {tabs.map(t => (
          <button 
            key={t.id} 
            onClick={() => setActiveTab(t.id)}
            style={{ 
              background: 'none', border: 'none', borderBottom: activeTab === t.id ? '2px solid var(--primary)' : '2px solid transparent', 
              padding: '12px 4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', 
              color: activeTab === t.id ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: activeTab === t.id ? 600 : 400 
            }}>
            <t.icon size={18} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="hod-content" style={{ marginTop: '-24px' }}>
        {activeTab === 'students' && <ResourcePage config={getConfig('students')} forcedFilters={{ branch_id: branchId }} />}
        {activeTab === 'teachers' && <ResourcePage config={getConfig('teachers')} forcedFilters={{ branch_id: branchId }} />}
        {activeTab === 'subjects' && <ResourcePage config={getConfig('subjects')} forcedFilters={{ branch_id: branchId }} />}
        {activeTab === 'timetable' && (
          <div style={{ marginTop: '48px' }}>
            <TimetablePage />
          </div>
        )}
      </div>
    </>
  )
}
