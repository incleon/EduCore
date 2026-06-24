import { useCallback, useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Plus, Check, X, Send, Eye } from 'lucide-react'
import { useAuth } from '../state/AuthContext'
import { api } from '../lib/api'
import './AssignmentsPage.css'

export default function AssignmentsPage() {
  const { user } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [selectedAssignment, setSelectedAssignment] = useState(null)
  const [submissions, setSubmissions] = useState([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showSubmitModal, setShowSubmitModal] = useState(false)
  
  const [formData, setFormData] = useState({ title: '', description: '', due_date: '', faculty_assignment_id: '' })
  const [submissionContent, setSubmissionContent] = useState('')
  const [facultyAssignments, setFacultyAssignments] = useState([])

  const isTeacher = user?.roles?.includes('teacher')
  const isStudent = user?.roles?.includes('student')

  const fetchAssignments = useCallback(async () => {
    try {
      setLoading(true)
      const res = await api.get('/api/assignments')
      setAssignments(res)
    } catch {
      setError('Failed to load assignments')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchFacultyAssignments = useCallback(async () => {
    try {
      const res = await api.get('/api/academic/faculty-assignments?page_size=100')
      setFacultyAssignments(res.items || [])
    } catch (err) {
      console.error(err)
    }
  }, [])

  useEffect(() => {
    fetchAssignments()
    if (isTeacher) fetchFacultyAssignments()
  }, [fetchAssignments, fetchFacultyAssignments, isTeacher])

  const fetchSubmissions = async (assignmentId) => {
    try {
      const res = await api.get(`/api/assignments/${assignmentId}/submissions`)
      setSubmissions(res)
    } catch (err) {
      console.error(err)
    }
  }

  const handleCreateAssignment = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/assignments', {
        ...formData,
        due_date: new Date(formData.due_date).toISOString()
      })
      setShowCreateModal(false)
      fetchAssignments()
    } catch {
      alert('Failed to create assignment')
    }
  }

  const handleSubmitAssignment = async (e) => {
    e.preventDefault()
    try {
      await api.post(`/api/assignments/submissions/${selectedAssignment.id}/submit`, {
        content: submissionContent
      })
      setShowSubmitModal(false)
      fetchAssignments()
    } catch {
      alert('Failed to submit assignment')
    }
  }

  const handleReviewSubmission = async (subId, status) => {
    try {
      await api.post(`/api/assignments/submissions/${subId}/review`, { status, feedback: '' })
      fetchSubmissions(selectedAssignment.id)
    } catch {
      alert('Failed to review submission')
    }
  }

  if (loading) return <div className="p-8 text-center text-gray-500">Loading assignments...</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>

  return (
    <div className="assignments-page p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Assignments</h1>
          <p className="text-gray-500 mt-1">Manage and track your homework assignments.</p>
        </div>
        {isTeacher && (
          <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
            <Plus size={18} /> New Assignment
          </Button>
        )}
      </div>

      {!selectedAssignment ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assignments.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-100 shadow-sm">
              No assignments found.
            </div>
          ) : (
            assignments.map(assign => (
              <Card key={isStudent ? assign.assignment_id : assign.id} className="assignment-card hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <CardTitle className="text-xl">
                    {isStudent ? assign.assignment?.title : assign.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4 line-clamp-2">
                    {isStudent ? assign.assignment?.description : assign.description}
                  </p>
                  
                  <div className="flex justify-between items-center text-sm mb-4">
                    <span className="text-gray-500">Due: {new Date(isStudent ? assign.assignment?.due_date : assign.due_date).toLocaleDateString()}</span>
                    {isStudent && (
                      <span className={`px-3 py-1 rounded-full text-xs font-medium 
                        ${assign.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                          assign.status === 'submitted' ? 'bg-blue-100 text-blue-800' : 
                          assign.status === 'accepted' ? 'bg-green-100 text-green-800' : 
                          'bg-red-100 text-red-800'}`}>
                        {assign.status.toUpperCase()}
                      </span>
                    )}
                  </div>

                  {isTeacher ? (
                    <Button variant="outline" className="w-full flex items-center justify-center gap-2" onClick={() => {
                      setSelectedAssignment(assign)
                      fetchSubmissions(assign.id)
                    }}>
                      <Eye size={16} /> View Submissions
                    </Button>
                  ) : (
                    <Button 
                      disabled={assign.status !== 'pending'} 
                      className="w-full flex items-center justify-center gap-2" 
                      onClick={() => {
                        setSelectedAssignment(assign)
                        setShowSubmitModal(true)
                      }}
                    >
                      {assign.status === 'pending' ? <><Send size={16} /> Submit Now</> : 'Submitted'}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <div className="submissions-view animate-fade-in">
          <Button variant="ghost" onClick={() => setSelectedAssignment(null)} className="mb-4">
            ← Back to Assignments
          </Button>
          
          <Card>
            <CardHeader>
              <CardTitle>Submissions for: {selectedAssignment.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b text-gray-500 font-medium text-sm">
                      <th className="p-3">Student ID</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Submitted At</th>
                      <th className="p-3">Content</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {submissions.length === 0 ? (
                      <tr><td colSpan="5" className="p-4 text-center text-gray-400">No submissions yet</td></tr>
                    ) : submissions.map(sub => (
                      <tr key={sub.id} className="border-b hover:bg-gray-50">
                        <td className="p-3">{sub.student_id}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium 
                            ${sub.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                              sub.status === 'submitted' ? 'bg-blue-100 text-blue-800' : 
                              sub.status === 'accepted' ? 'bg-green-100 text-green-800' : 
                              'bg-red-100 text-red-800'}`}>
                            {sub.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 text-sm text-gray-500">
                          {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString() : '-'}
                        </td>
                        <td className="p-3 text-sm max-w-xs truncate" title={sub.content}>
                          {sub.content || '-'}
                        </td>
                        <td className="p-3 text-right">
                          {sub.status === 'submitted' && (
                            <div className="flex gap-2 justify-end">
                              <Button size="sm" onClick={() => handleReviewSubmission(sub.id, 'accepted')} className="bg-green-500 hover:bg-green-600 px-2 py-1 h-auto text-xs">
                                <Check size={14} /> Accept
                              </Button>
                              <Button size="sm" onClick={() => handleReviewSubmission(sub.id, 'rejected')} variant="destructive" className="px-2 py-1 h-auto text-xs">
                                <X size={14} /> Reject
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modals */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md animate-scale-up">
            <h2 className="text-2xl font-bold mb-4">New Assignment</h2>
            <form onSubmit={handleCreateAssignment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input required type="text" className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 h-24" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input required type="datetime-local" className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500" value={formData.due_date} onChange={e => setFormData({...formData, due_date: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assign To Section (Faculty Allocation)</label>
                <select required className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500" value={formData.faculty_assignment_id} onChange={e => setFormData({...formData, faculty_assignment_id: e.target.value})}>
                  <option value="">Select a class/section</option>
                  {facultyAssignments.map(fa => (
                    <option key={fa.id} value={fa.id}>{fa.curriculum_subject?.subject?.name} - {fa.academic_year}</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button type="submit">Create</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showSubmitModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md animate-scale-up">
            <h2 className="text-2xl font-bold mb-4">Submit Assignment</h2>
            <p className="text-sm text-gray-500 mb-4">For: {selectedAssignment.assignment?.title}</p>
            <form onSubmit={handleSubmitAssignment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Your Submission (Text or Link)</label>
                <textarea required className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 h-32" value={submissionContent} onChange={e => setSubmissionContent(e.target.value)} placeholder="Type your response or paste a Google Drive link here..." />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="ghost" onClick={() => setShowSubmitModal(false)}>Cancel</Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700"><Send size={16} className="mr-2"/> Submit Work</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
