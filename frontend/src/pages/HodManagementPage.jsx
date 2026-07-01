import { useEffect, useState, useMemo } from 'react'
import { LoaderCircle, CheckCircle2, Building2, BookOpen, Users, UserCog, Network } from 'lucide-react'
import { api } from '../lib/api'
import PageHeader from '../components/ui/PageHeader'
import { useAuth } from '../state/AuthContext'

export default function HodManagementPage() {
  const { can } = useAuth()
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [branches, setBranches] = useState([])
  const [professors, setProfessors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [savingId, setSavingId] = useState(null)

  const [selectedDeptId, setSelectedDeptId] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState('')

  useEffect(() => {
    if (!can('manage_academic_structure')) return
    Promise.all([
      api.get('/api/departments?page=1&page_size=100'),
      api.get('/api/courses?page=1&page_size=100'),
      api.get('/api/academic/branches?page=1&page_size=100'),
      api.get('/api/teachers?page=1&page_size=100')
    ]).then(([dRes, cRes, bRes, tRes]) => {
      setDepartments(dRes.items || [])
      setCourses(cRes.items || [])
      setBranches(bRes.items || [])
      setProfessors((tRes.items || []).filter(t => ['Professor', 'Assistant Professor', 'Associate Professor'].includes(t.designation)))
      setLoading(false)
    }).catch(err => {
      setError(err.message)
      setLoading(false)
    })
  }, [can])

  const assignHod = async (branchId, teacherId) => {
    setSavingId(branchId)
    try {
      const branch = branches.find(b => b.id === branchId)
      await api.put(`/api/academic/branches/${branchId}`, { 
        name: branch.name, 
        code: branch.code, 
        description: branch.description, 
        hod_id: teacherId || null 
      })
      setToast('HOD assigned successfully!')
      setTimeout(() => setToast(''), 3000)
      
      // Update local state
      setBranches(branches.map(b => b.id === branchId ? { ...b, hod_id: teacherId || null } : b))
    } catch (err) {
      alert(err.message)
    } finally {
      setSavingId(null)
    }
  }

  // Filtering Logic
  const filteredCourses = useMemo(() => {
    if (!selectedDeptId) return courses
    return courses.filter(c => c.department_id === Number(selectedDeptId))
  }, [courses, selectedDeptId])

  const filteredBranches = useMemo(() => {
    let result = branches
    if (selectedDeptId) {
      result = result.filter(b => b.department_id === Number(selectedDeptId))
    }
    if (selectedCourseId) {
      result = result.filter(b => b.course_id === Number(selectedCourseId))
    }
    return result
  }, [branches, selectedDeptId, selectedCourseId])

  // Get assigned HODs for the summary view
  const assignedBranches = useMemo(() => {
    return filteredBranches.filter(b => b.hod_id)
  }, [filteredBranches])

  if (!can('manage_academic_structure')) return <div className="inline-error">You do not have permission to manage HODs.</div>
  if (loading) return <div className="content-loader"><LoaderCircle className="spin" /><span>Loading HOD configuration</span></div>

  return (
    <>
      <PageHeader 
        eyebrow="ADMINISTRATION" 
        title="HOD Management" 
        description="Streamlined assignment of Heads of Departments across branches." 
      />
      {error && <div className="inline-error">{error}</div>}
      
      {/* Tiered Selection Flow */}
      <div className="panel" style={{ padding: '24px', marginBottom: '24px', background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', color: 'var(--text-1)' }}>
          <Network size={20} color="var(--primary)" /> Academic Structure Drill-down
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          
          {/* Department Selection */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Building2 size={14} /> 1. Select Department
            </label>
            <select 
              value={selectedDeptId} 
              onChange={(e) => {
                setSelectedDeptId(e.target.value);
                setSelectedCourseId(''); // Reset course when dept changes
              }}
              className="form-control"
              style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface-1)' }}
            >
              <option value="">All Departments</option>
              {departments.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {/* Course Selection */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '13px', fontWeight: 600, color: selectedDeptId ? 'var(--text-2)' : 'var(--text-3)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <BookOpen size={14} /> 2. Select Course
            </label>
            <select 
              value={selectedCourseId} 
              onChange={(e) => setSelectedCourseId(e.target.value)}
              disabled={!selectedDeptId && departments.length > 0}
              className="form-control"
              style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--border)', background: (!selectedDeptId && departments.length > 0) ? 'var(--surface-3)' : 'var(--surface-1)' }}
            >
              <option value="">{selectedDeptId ? 'All Courses in Department' : 'Select a Department first'}</option>
              {filteredCourses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Assignment Section */}
      <h3 style={{ marginTop: '32px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', color: 'var(--text-1)' }}>
        <UserCog size={20} color="var(--primary)" /> Manage Branch HODs
      </h3>
      
      {filteredBranches.length === 0 ? (
        <div className="panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-3)' }}>
          <p>No branches found for the selected criteria.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px', marginBottom: '40px' }}>
          {filteredBranches.map(branch => {
            const currentHodId = branch.hod_id || ''
            
            return (
              <div key={branch.id} className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', borderTop: currentHodId ? '4px solid var(--mint)' : '4px solid var(--border)', transition: 'all 0.2s ease', position: 'relative', overflow: 'hidden' }}>
                
                {/* Branch Header */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h4 style={{ margin: 0, fontSize: '16px', color: 'var(--text-1)' }}>{branch.name}</h4>
                    {currentHodId && <CheckCircle2 size={18} color="var(--mint)" style={{ flexShrink: 0 }} />}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: '4px' }}>
                    {branch.course?.name} • {branch.code}
                  </div>
                </div>

                {/* Assignment Dropdown */}
                <div style={{ marginTop: 'auto' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-2)', display: 'block', marginBottom: '6px' }}>Assigned Head</label>
                  <select 
                    value={currentHodId}
                    onChange={(e) => assignHod(branch.id, e.target.value ? Number(e.target.value) : null)}
                    disabled={savingId === branch.id}
                    className="form-control"
                    style={{ width: '100%', padding: '10px', borderRadius: '6px', border: currentHodId ? '1px solid var(--mint)' : '1px solid var(--border)', background: 'var(--surface-1)', fontSize: '14px' }}
                  >
                    <option value="">-- Unassigned --</option>
                    {professors.map(prof => (
                      <option key={prof.id} value={prof.id}>{prof.user?.full_name} ({prof.designation})</option>
                    ))}
                  </select>
                </div>
                
                {savingId === branch.id && (
                  <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(255,255,255,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(2px)' }}>
                    <LoaderCircle className="spin" color="var(--primary)" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Professional Summary Section */}
      <h3 style={{ marginTop: '32px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', color: 'var(--text-1)' }}>
        <Users size={20} color="var(--primary)" /> HOD Summary Directory
      </h3>
      
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        {assignedBranches.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-3)' }}>
            No HODs assigned yet in this selection.
          </div>
        ) : (
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: 'var(--text-2)', fontWeight: 600 }}>Branch & Course</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: 'var(--text-2)', fontWeight: 600 }}>Head of Department</th>
                <th style={{ padding: '16px', textAlign: 'center', fontSize: '12px', color: 'var(--text-2)', fontWeight: 600 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {assignedBranches.map((branch, idx) => {
                const hod = professors.find(p => p.id === branch.hod_id)
                return (
                  <tr key={branch.id} style={{ borderBottom: idx === assignedBranches.length - 1 ? 'none' : '1px solid var(--border)' }}>
                    <td style={{ padding: '16px' }}>
                      <div style={{ fontWeight: 500, color: 'var(--text-1)' }}>{branch.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>{branch.course?.name}</div>
                    </td>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '14px' }}>
                          {hod?.user?.full_name?.charAt(0) || 'U'}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-1)' }}>{hod?.user?.full_name || 'Unknown User'}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>{hod?.designation || 'Staff'}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '16px', textAlign: 'center' }}>
                      <span className="status-badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--mint)', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                        Active Role
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      
      {toast && (
        <div className="toast" style={{ position: 'fixed', bottom: '24px', right: '24px', background: 'var(--surface-1)', border: '1px solid var(--mint)', color: 'var(--mint)', padding: '12px 20px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 1000 }}>
          <CheckCircle2 size={18} /> 
          <span style={{ fontWeight: 500 }}>{toast}</span>
        </div>
      )}
    </>
  )
}
