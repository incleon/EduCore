import { useEffect, useMemo, useState } from 'react'
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Info, LoaderCircle } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../state/AuthContext'
import PageHeader from '../components/ui/PageHeader'
import ResourcePage from './ResourcePage'
import { resourceConfigs } from '../config/resources'
import './AttendancePage.css'

function StudentAttendanceCalendar() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attendanceRecords, setAttendanceRecords] = useState([])
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState(new Date())
  
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const profile = await api.get('/auth/profile')
        if (profile.student?.id) {
          let allRecords = []
          let page = 1
          let hasMore = true
          while (hasMore) {
            const res = await api.get(`/api/attendance?student_id=${profile.student.id}&page=${page}&page_size=100`)
            if (res.items && res.items.length > 0) {
              allRecords = [...allRecords, ...res.items]
              if (res.items.length < 100) hasMore = false
              else page++
            } else {
              hasMore = false
            }
          }
          setAttendanceRecords(allRecords)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate()
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay()

  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]

  // Map attendance records by YYYY-MM-DD
  const attendanceByDate = useMemo(() => {
    const map = {}
    attendanceRecords.forEach(record => {
      const dateStr = record.date // YYYY-MM-DD
      if (!map[dateStr]) map[dateStr] = []
      map[dateStr].push(record)
    })
    return map
  }, [attendanceRecords])

  const renderCalendar = () => {
    const days = []
    
    // Fill empty spots for first week
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>)
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const dateObj = new Date(currentDate.getFullYear(), currentDate.getMonth(), d)
      const dateStr = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`
      const records = attendanceByDate[dateStr] || []
      
      const dayOfWeek = dateObj.getDay()
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
      let statusClass = ''
      
      // Determine coloring based on priorities
      if (isWeekend) {
        statusClass = 'weekend'
      } else if (records.length > 0) {
        // If at least one absent, mark red, else if holiday blue, else green
        const hasAbsent = records.some(r => String(r.status?.value || r.status).toLowerCase() === 'absent')
        const hasHoliday = records.some(r => String(r.status?.value || r.status).toLowerCase() === 'holiday')
        if (hasAbsent) {
          statusClass = 'absent'
        } else if (hasHoliday) {
          statusClass = 'holiday'
        } else {
          statusClass = 'present'
        }
      }

      const isSelected = selectedDate.getDate() === d && 
                         selectedDate.getMonth() === currentDate.getMonth() && 
                         selectedDate.getFullYear() === currentDate.getFullYear()

      days.push(
        <div 
          key={d} 
          className={`calendar-day ${statusClass} ${isSelected ? 'selected' : ''}`}
          onClick={() => setSelectedDate(dateObj)}
        >
          <span className="day-number">{d}</span>
          {records.length > 0 && <span className="record-dot"></span>}
        </div>
      )
    }
    return days
  }

  const selectedDateStr = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`
  const selectedRecords = attendanceByDate[selectedDateStr] || []
  const isSelectedWeekend = selectedDate.getDay() === 0 || selectedDate.getDay() === 6

  return (
    <>
      <PageHeader 
        eyebrow="ATTENDANCE OVERVIEW" 
        title="My Attendance" 
        description="Track your daily presence, absences, and overall attendance record." 
      />
      {error && <div className="inline-error">{error}</div>}
      
      {loading ? (
        <div className="content-loader"><LoaderCircle className="spin" /><span>Loading attendance data...</span></div>
      ) : (
        <div className="attendance-calendar-container">
          <article className="calendar-panel">
            <div className="calendar-header">
              <h2>{monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}</h2>
              <div className="calendar-nav-buttons">
                <button onClick={prevMonth} aria-label="Previous Month"><ChevronLeft size={18} /></button>
                <button onClick={nextMonth} aria-label="Next Month"><ChevronRight size={18} /></button>
              </div>
            </div>
            
            <div className="calendar-grid">
              <div className="calendar-day-header">Sun</div>
              <div className="calendar-day-header">Mon</div>
              <div className="calendar-day-header">Tue</div>
              <div className="calendar-day-header">Wed</div>
              <div className="calendar-day-header">Thu</div>
              <div className="calendar-day-header">Fri</div>
              <div className="calendar-day-header">Sat</div>
              
              {renderCalendar()}
            </div>
            
            <div className="attendance-legend">
              <div className="legend-item"><span className="legend-color present"></span> Present</div>
              <div className="legend-item"><span className="legend-color absent"></span> Absent</div>
              <div className="legend-item"><span className="legend-color holiday"></span> Holiday</div>
              <div className="legend-item"><span className="legend-color weekend"></span> Weekend</div>
            </div>
          </article>
          
          <aside className="details-panel">
            <h3><CalendarIcon size={18} /> {monthNames[selectedDate.getMonth()]} {selectedDate.getDate()}, {selectedDate.getFullYear()}</h3>
            
            {isSelectedWeekend && selectedRecords.length === 0 ? (
              <div className="details-empty">
                <Info size={32} />
                <p>Weekend</p>
              </div>
            ) : selectedRecords.length === 0 ? (
              <div className="details-empty">
                <Info size={32} />
                <p>No attendance records found for this date.</p>
              </div>
            ) : (
              <div className="attendance-details-list">
                {selectedRecords.map((record, idx) => (
                  <div className="attendance-record-item" key={idx}>
                    <div className="attendance-record-info">
                      <strong>{record.subject?.name || 'Subject'}</strong>
                      <span>{record.teacher?.user?.full_name || 'Faculty'}</span>
                    </div>
                    <span className={`status-badge ${String(record.status?.value || record.status).toLowerCase()}`}>
                      {String(record.status?.value || record.status).toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </aside>
        </div>
      )}
    </>
  )
}

export default function AttendancePage({ forcedFilters = {} }) {
  const { user } = useAuth()
  
  if (user?.roles?.includes('student')) {
    return <StudentAttendanceCalendar />
  }

  const config = resourceConfigs.find((c) => c.slug === 'attendance')
  return <ResourcePage config={config} forcedFilters={forcedFilters} />
}
