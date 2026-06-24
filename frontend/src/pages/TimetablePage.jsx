import { CalendarRange, LoaderCircle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/ui/PageHeader'
import { api } from '../lib/api'

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const periods = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00']

export default function TimetablePage() {
  const [data, setData] = useState(null)
  const [department, setDepartment] = useState('')
  const [semester, setSemester] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true); setError('')
    const params = new URLSearchParams()
    if (department) params.set('department_id', department)
    if (semester) params.set('semester', semester)
    api.get(`/api/timetables?${params}`).then((payload) => {
      setData(payload)
      if (!department && payload.current_department_id) setDepartment(String(payload.current_department_id))
      if (!semester && payload.current_semester) setSemester(String(payload.current_semester))
    }).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [department, semester])

  const slotMap = useMemo(() => new Map((data?.slots || []).map((slot) => [`${slot.day_of_week}-${slot.slot_index}`, slot])), [data])

  return <>
    <PageHeader eyebrow="LEARNING" title="Timetable" description="The weekly teaching rhythm for your department and semester." actions={data?.version && <span className={`status-badge ${data.version.status}`}>{data.version.status}</span>} />
    <section className="panel timetable-panel">
      <div className="timetable-toolbar">
        <label><span>Department</span><select value={department} onChange={(event) => setDepartment(event.target.value)}><option value="">Select department</option>{data?.departments?.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
        <label><span>Semester</span><select value={semester} onChange={(event) => setSemester(event.target.value)}><option value="">Select semester</option>{[1,2,3,4,5,6,7,8].map((item) => <option key={item} value={item}>Semester {item}</option>)}</select></label>
      </div>
      {loading ? <div className="table-state"><LoaderCircle className="spin" /> Loading timetable</div>
        : error ? <div className="table-state error">{error}</div>
        : !department || !semester ? <div className="table-state"><CalendarRange size={24} /><strong>Choose a department and semester</strong><span>The weekly grid will appear here.</span></div>
        : <div className="timetable-scroll"><div className="timetable-grid"><div className="grid-corner">Day</div>{periods.map((period) => <div className="period-head" key={period}>{period}</div>)}{days.map((day, dayIndex) => [<div className="day-head" key={`${day}-head`}>{day}</div>, ...periods.map((_, periodIndex) => { const slot = slotMap.get(`${dayIndex + 1}-${periodIndex + 1}`); return <div className={`schedule-slot ${slot?.subject ? 'occupied' : ''}`} key={`${day}-${periodIndex}`}>{slot?.subject ? <><strong>{slot.subject.code}</strong><span>{slot.subject.name}</span><small>{slot.teacher?.name || 'Faculty TBD'}</small></> : <span className="free-slot">—</span>}</div> })])}</div></div>}
    </section>
  </>
}
