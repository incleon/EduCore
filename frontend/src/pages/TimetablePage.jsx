import { CalendarRange, LoaderCircle, Save, Download, Edit2, User } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/ui/PageHeader'
import { api } from '../lib/api'
import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const periods = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
const LUNCH_INDEX = 4; // 13:00 - 14:00

export default function TimetablePage() {
  const [data, setData] = useState(null)
  const [department, setDepartment] = useState('')
  const [course, setCourse] = useState('')
  const [section, setSection] = useState('')
  const [semester, setSemester] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [selectedVersionId, setSelectedVersionId] = useState('')
  
  // Teacher mode states
  const [viewMode, setViewMode] = useState('class') // 'class' or 'teacher'
  const [teacherSchedule, setTeacherSchedule] = useState([])
  const [loadingTeacher, setLoadingTeacher] = useState(false)
  const [initialCheck, setInitialCheck] = useState(false)

  const [editableSlots, setEditableSlots] = useState([])

  // Reset version selection when scope changes
  useEffect(() => {
    setSelectedVersionId('')
    setIsEditMode(false)
  }, [department, course, semester, section])

  useEffect(() => {
    if (viewMode === 'teacher' && teacherSchedule.length === 0) {
      setLoadingTeacher(true)
      api.get('/api/timetables/teacher').then(res => {
         setTeacherSchedule(res.slots || [])
      }).catch(err => console.error(err)).finally(() => setLoadingTeacher(false))
    }
  }, [viewMode, teacherSchedule.length])

  useEffect(() => {
    setLoading(true); setError('')
    const params = new URLSearchParams()
    if (department) params.set('department_id', department)
    if (course) params.set('course_id', course)
    if (section) params.set('section_id', section)
    if (semester) params.set('semester', semester)
    if (selectedVersionId) params.set('version_id', selectedVersionId)
    
    api.get(`/api/timetables?${params}`).then((payload) => {
      setData(payload)
      if (!department && payload.current_department_id) setDepartment(String(payload.current_department_id))
      if (!course && payload.current_course_id) setCourse(String(payload.current_course_id))
      if (!section && payload.current_section_id) setSection(String(payload.current_section_id))
      if (!semester && payload.current_semester) setSemester(String(payload.current_semester))
      
      setEditableSlots(payload.slots || [])
      
      // Auto-select version id if not selected and a version exists
      if (payload.version && !selectedVersionId) {
        setSelectedVersionId(String(payload.version.id))
      }
      
      // If there's no version, we auto-start in edit mode if admin
      if (!payload.version && payload.subjects?.length > 0) {
        setIsEditMode(true)
      } else {
        setIsEditMode(false)
      }
      
      if (payload.is_teacher && !initialCheck) {
        setViewMode('teacher')
        setInitialCheck(true)
      }
      
    }).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [department, course, semester, section, selectedVersionId, initialCheck])

  const slotMap = useMemo(() => new Map(editableSlots.map((slot) => [`${slot.day_of_week}-${slot.slot_index}`, slot])), [editableSlots])
  const teacherSlotMap = useMemo(() => new Map(teacherSchedule.map((slot) => [`${slot.day_of_week}-${slot.slot_index}`, slot])), [teacherSchedule])

  const handleSlotChange = (dayIndex, periodIndex, field, value) => {
    const day_of_week = dayIndex + 1;
    const slot_index = periodIndex + 1;
    const existingSlotIndex = editableSlots.findIndex(s => s.day_of_week === day_of_week && s.slot_index === slot_index);
    
    let newSlots = [...editableSlots];
    if (existingSlotIndex >= 0) {
      newSlots[existingSlotIndex] = { ...newSlots[existingSlotIndex], [field]: value ? parseInt(value) : null };
      if (!newSlots[existingSlotIndex].subject_id && !newSlots[existingSlotIndex].teacher_id) {
         newSlots.splice(existingSlotIndex, 1);
      }
    } else {
      newSlots.push({ 
        day_of_week, 
        slot_index, 
        subject_id: field === 'subject_id' ? parseInt(value) : null, 
        teacher_id: field === 'teacher_id' ? parseInt(value) : null 
      });
    }
    setEditableSlots(newSlots);
  }

  const handleSave = async () => {
    if (!department || !course || !semester || !section) {
      alert('Please select department, course, semester, and section to save timetable');
      return;
    }
    setSaving(true);
    try {
      const slotsPayload = editableSlots.map(s => ({
        day_of_week: s.day_of_week,
        slot_index: s.slot_index,
        subject_id: s.subject_id || (s.subject ? s.subject.id : null),
        teacher_id: s.teacher_id || (s.teacher ? s.teacher.id : null)
      })).filter(s => s.subject_id || s.teacher_id);
      
      await api.post('/api/timetables/version', {
        department_id: parseInt(department),
        course_id: parseInt(course),
        section_id: parseInt(section),
        semester: parseInt(semester),
        action: 'submit',
        slots: slotsPayload
      });
      alert('Timetable saved successfully!');
      
      // Reload to reflect new version
      setSelectedVersionId('')
      setLoading(true)
      const params = new URLSearchParams()
      params.set('department_id', department)
      params.set('course_id', course)
      params.set('section_id', section)
      params.set('semester', semester)
      const payload = await api.get(`/api/timetables?${params}`)
      setData(payload)
      setEditableSlots(payload.slots || [])
      setIsEditMode(false)
      if (payload.version) setSelectedVersionId(String(payload.version.id))
      setLoading(false)

    } catch (e) {
      alert('Failed to save: ' + e.message);
      setSaving(false);
    }
  }

  // Configurable Institute Name for PDF Export
  const INSTITUTE_NAME = "Your Institute Name Here";

  const exportPDF = () => {
    const doc = new jsPDF('landscape');
    
    if (viewMode === 'teacher') {
      doc.setFontSize(16);
      doc.text(INSTITUTE_NAME, doc.internal.pageSize.width / 2, 15, { align: 'center' });
      
      doc.setFontSize(12);
      doc.text("My Teaching Schedule", doc.internal.pageSize.width / 2, 22, { align: 'center' });
      
      const tableBody = days.map((day, dayIndex) => {
        const row = [day];
        periods.forEach((period, periodIndex) => {
          if (periodIndex === LUNCH_INDEX) {
            row.push('Lunch Break');
          } else {
            const slot = teacherSlotMap.get(`${dayIndex + 1}-${periodIndex + 1}`);
            if (slot && slot.subject) {
              row.push(`${slot.subject.code}\n${slot.subject.name}\nSem ${slot.semester} ${slot.branch?.code || ''} Sec ${slot.section?.code || ''}`);
            } else {
              row.push('-');
            }
          }
        });
        return row;
      });
      const head = [['Day', ...periods]];
      autoTable(doc, {
        head: head, body: tableBody, startY: 28, theme: 'grid',
        styles: { font: 'helvetica', fontSize: 9, cellPadding: 3, halign: 'center', valign: 'middle', lineColor: [200, 200, 200] },
        headStyles: { fillColor: [41, 128, 185], textColor: 255, fontStyle: 'bold' },
        columnStyles: { 0: { fontStyle: 'bold', fillColor: [240, 245, 250], textColor: [40, 40, 40] }, [LUNCH_INDEX + 1]: { fillColor: [220, 220, 220], textColor: [100, 100, 100], fontStyle: 'italic' } },
        didParseCell: function(data) {
          if (data.section === 'body' && data.column.index > 0 && data.column.index !== LUNCH_INDEX + 1) {
            if (data.cell.raw === '-') {
              data.cell.text = ['FREE PERIOD'];
              data.cell.styles.textColor = [150, 150, 150]; // Subtle grey for free period
            } else {
              data.cell.styles.fontStyle = 'bold';
              data.cell.styles.textColor = [40, 40, 40];
            }
          }
        }
      });
      doc.save(`My_Schedule.pdf`);
    } else {
      const deptObj = data?.departments?.find(d => d.id == department);
      const courseObj = data?.courses?.find(c => c.id == course);
      const secObj = data?.sections?.find(s => s.id == section);
      
      doc.setFontSize(16);
      doc.text(INSTITUTE_NAME, doc.internal.pageSize.width / 2, 15, { align: 'center' });
      
      doc.setFontSize(12);
      if (deptObj) doc.text(`Department of ${deptObj.name}`, doc.internal.pageSize.width / 2, 22, { align: 'center' });
      
      doc.setFontSize(11);
      let subTitle = `Program: ${courseObj?.name || ''}   |   Semester: ${semester}   |   Section: ${secObj?.code || ''}`;
      doc.text(subTitle, doc.internal.pageSize.width / 2, 28, { align: 'center' });
      
      if (data?.version) {
        doc.setFontSize(10);
        doc.text(`(Version ${data.version.version_number} - ${data.version.status.toUpperCase()})`, doc.internal.pageSize.width / 2, 33, { align: 'center' });
      }
      
      const tableBody = days.map((day, dayIndex) => {
        const row = [day];
        periods.forEach((period, periodIndex) => {
          if (periodIndex === LUNCH_INDEX) {
            row.push('Lunch Break');
          } else {
            const slot = slotMap.get(`${dayIndex + 1}-${periodIndex + 1}`);
            if (slot && (slot.subject || slot.subject_id)) {
              const subjectObj = data.subjects?.find(s => s.id === (slot.subject_id || slot.subject?.id)) || slot.subject;
              const teacherObj = data.teachers?.find(t => t.id === (slot.teacher_id || slot.teacher?.id)) || slot.teacher;
              row.push(`${subjectObj?.code || ''}\n${subjectObj?.name || ''}\n${teacherObj?.name || ''}`);
            } else {
              row.push('-');
            }
          }
        });
        return row;
      });

      const head = [['Day', ...periods]];

      autoTable(doc, {
        head: head,
        body: tableBody,
        startY: 38,
        theme: 'grid',
        styles: { font: 'helvetica', fontSize: 9, cellPadding: 3, halign: 'center', valign: 'middle', lineColor: [200, 200, 200] },
        headStyles: { fillColor: [41, 128, 185], textColor: 255, fontStyle: 'bold' },
        columnStyles: {
          0: { fontStyle: 'bold', fillColor: [240, 245, 250], textColor: [40, 40, 40] },
          [LUNCH_INDEX + 1]: { fillColor: [220, 220, 220], textColor: [100, 100, 100], fontStyle: 'italic' }
        },
        didParseCell: function(data) {
          if (data.section === 'body' && data.column.index > 0 && data.column.index !== LUNCH_INDEX + 1) {
            if (data.cell.raw === '-') {
              data.cell.text = ['FREE PERIOD'];
              data.cell.styles.textColor = [150, 150, 150]; // Subtle grey for free period
            } else {
              data.cell.styles.fontStyle = 'bold';
              data.cell.styles.textColor = [40, 40, 40];
            }
          }
        }
      });

      doc.save(`Timetable_Sem${semester}_Sec${secObj?.code || ''}_V${data?.version?.version_number || 1}.pdf`);
    }
  };

  const isAdmin = data?.subjects?.length > 0;

  return <>
    <PageHeader eyebrow="LEARNING" title="Timetable" description="The weekly teaching rhythm for your department and semester." actions={
      <div style={{ display: 'flex', gap: '10px' }}>
        {data?.is_teacher && (
          <div className="tab-buttons" style={{ display: 'flex', background: 'var(--surface)', borderRadius: '6px', border: '1px solid var(--border)', overflow: 'hidden', marginRight: '10px' }}>
            <button className={`tab-btn ${viewMode === 'teacher' ? 'active' : ''}`} onClick={() => setViewMode('teacher')} style={{ padding: '6px 12px', border: 'none', background: viewMode === 'teacher' ? 'var(--primary)' : 'transparent', color: viewMode === 'teacher' ? 'white' : 'var(--ink)', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}><User size={14}/> My Schedule</button>
          </div>
        )}
        
        {viewMode === 'class' && isAdmin && data?.version && !isEditMode && <button className="primary-button" onClick={() => setIsEditMode(true)}><Edit2 size={16}/> Modify Timetable</button>}
        {viewMode === 'class' && isAdmin && isEditMode && <button className="primary-button" onClick={handleSave} disabled={saving}><Save size={16}/> {saving ? 'Saving...' : 'Save'}</button>}
        
        {((viewMode === 'class' && editableSlots.length > 0) || (viewMode === 'teacher' && teacherSchedule.length > 0)) && <button className="secondary-button" onClick={exportPDF}><Download size={16}/> Export PDF</button>}
      </div>
    } />
    
    {viewMode === 'teacher' ? (
      <section className="panel timetable-panel">
        <div className="timetable-toolbar" style={{ padding: '1rem', borderBottom: '1px solid var(--border)', background: 'var(--surface-hover)' }}>
           <strong>Your Personal Teaching Schedule</strong>
           <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--ink-light)' }}>This grid consolidates all your classes across different sections and semesters.</p>
        </div>
        {loadingTeacher ? <div className="table-state"><LoaderCircle className="spin" /> Loading schedule...</div> :
          teacherSchedule.length === 0 ? <div className="table-state"><CalendarRange size={24} /><strong>No Classes Scheduled</strong><span>You do not have any assigned classes in the current active timetables.</span></div> :
          <div className="timetable-scroll">
            <div className="timetable-grid" style={{ gridTemplateColumns: `80px repeat(${periods.length}, minmax(140px, 1fr))` }}>
              <div className="grid-corner">Day</div>
              {periods.map((period) => <div className="period-head" key={period}>{period}</div>)}
              {days.map((day, dayIndex) => [
                <div className="day-head" key={`${day}-head`}>{day}</div>, 
                ...periods.map((_, periodIndex) => { 
                  if (periodIndex === LUNCH_INDEX) {
                    return <div className="schedule-slot lunch-slot" key={`${day}-${periodIndex}`} style={{ backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}><strong>Lunch Break</strong></div>
                  }
                  const slot = teacherSlotMap.get(`${dayIndex + 1}-${periodIndex + 1}`); 
                  
                  return (
                    <div className={`schedule-slot ${slot?.subject ? 'occupied' : ''}`} key={`${day}-${periodIndex}`}>
                      {slot?.subject ? <>
                        <strong>{slot.subject.code}</strong>
                        <span title={slot.subject.name} style={{overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', width:'100%'}}>{slot.subject.name}</span>
                        <small style={{ color: 'var(--primary)', fontWeight: 'bold' }}>
                          Sem {slot.semester} {slot.branch?.code || ''} {slot.section?.code ? `Sec ${slot.section.code}` : ''}
                        </small>
                      </> : <span className="free-slot">—</span>}
                    </div>
                  ) 
                })
              ])}
            </div>
          </div>
        }
      </section>
    ) : (
      <section className="panel timetable-panel">
        {!data?.is_student && (
          <div className="timetable-toolbar" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', padding: '1rem', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
            <label><span>Department</span><select value={department} onChange={(e) => setDepartment(e.target.value)}><option value="">Select</option>{data?.departments?.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
            <label><span>Course</span><select value={course} onChange={(e) => setCourse(e.target.value)}><option value="">Select</option>{data?.courses?.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
            <label><span>Semester</span><select value={semester} onChange={(e) => setSemester(e.target.value)}><option value="">Select</option>{[1,2,3,4,5,6,7,8].map((item) => <option key={item} value={item}>Sem {item}</option>)}</select></label>
            {data?.sections && <label><span>Section</span><select value={section} onChange={(e) => setSection(e.target.value)}><option value="">Select</option>{data.sections.filter(s => s.course_id == course && s.semester == semester).map((item) => <option value={item.id} key={item.id}>{item.code}</option>)}</select></label>}
            
            {data?.versions_history?.length > 1 && (
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--ink)' }}>Version History:</span>
                <select value={selectedVersionId} onChange={(e) => setSelectedVersionId(e.target.value)} style={{ padding: '6px', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}>
                  {data.versions_history.map(v => (
                    <option key={v.id} value={v.id}>
                      Version {v.version_number} ({v.status})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}
        {loading ? <div className="table-state"><LoaderCircle className="spin" /> Loading timetable</div>
          : error ? <div className="table-state error">{error}</div>
          : !department || !semester || !course || !section ? <div className="table-state"><CalendarRange size={24} /><strong>Select all options</strong><span>Choose department, course, semester, and section to view or edit the timetable.</span></div>
          : <div className="timetable-scroll">
              <div className="timetable-grid" style={{ gridTemplateColumns: `80px repeat(${periods.length}, minmax(140px, 1fr))` }}>
                <div className="grid-corner">Day</div>
                {periods.map((period) => <div className="period-head" key={period}>{period}</div>)}
                {days.map((day, dayIndex) => [
                  <div className="day-head" key={`${day}-head`}>{day}</div>, 
                  ...periods.map((_, periodIndex) => { 
                    if (periodIndex === LUNCH_INDEX) {
                      return <div className="schedule-slot lunch-slot" key={`${day}-${periodIndex}`} style={{ backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}><strong>Lunch Break</strong></div>
                    }
                    const slot = slotMap.get(`${dayIndex + 1}-${periodIndex + 1}`); 
                    const currentSubj = slot?.subject_id || slot?.subject?.id || '';
                    const currentTeacher = slot?.teacher_id || slot?.teacher?.id || '';
                    
                    if (isAdmin && isEditMode) {
                      return (
                        <div className="schedule-slot editable-slot" key={`${day}-${periodIndex}`} style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '4px' }}>
                          <select value={currentSubj} onChange={(e) => handleSlotChange(dayIndex, periodIndex, 'subject_id', e.target.value)} className="slot-select">
                            <option value="">[ Free Period ]</option>
                            {data.subjects?.map(s => <option key={s.id} value={s.id}>{s.code}</option>)}
                          </select>
                          <select value={currentTeacher} onChange={(e) => handleSlotChange(dayIndex, periodIndex, 'teacher_id', e.target.value)} className="slot-select">
                            <option value="">- Teacher -</option>
                            {data.teachers?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                          </select>
                        </div>
                      )
                    }
                    
                    return (
                      <div className={`schedule-slot ${slot?.subject ? 'occupied' : ''}`} key={`${day}-${periodIndex}`}>
                        {slot?.subject ? <><strong>{slot.subject.code}</strong><span>{slot.subject.name}</span><small>{slot.teacher?.name || 'Faculty TBD'}</small></> : <span className="free-slot">—</span>}
                      </div>
                    ) 
                  })
                ])}
              </div>
            </div>}
      </section>
    )}
  </>
}
