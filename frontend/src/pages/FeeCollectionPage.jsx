import { useState, useEffect, useMemo } from 'react'
import { Search, UserRound, CheckCircle2, AlertCircle, WalletCards, ReceiptIndianRupee, IndianRupee } from 'lucide-react'
import { api } from '../lib/api'
import PageHeader from '../components/ui/PageHeader'
import './FeeCollectionPage.css'

export default function FeeCollectionPage() {
  const [students, setStudents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStudent, setSelectedStudent] = useState(null)
  
  const [invoices, setInvoices] = useState([])
  const [loadingInvoices, setLoadingInvoices] = useState(false)
  const [paymentLoading, setPaymentLoading] = useState(false)
  
  // Payment Form State
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState('cash')
  const [payRef, setPayRef] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    // Load students for the search dropdown
    api.get('/api/students?page=1&page_size=100')
      .then(res => setStudents(res.items || res))
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (selectedStudent) {
      setLoadingInvoices(true)
      api.get(`/api/finance/student-fees?student_id=${selectedStudent.id}`)
        .then(data => {
          // data might be wrapped in pagination if standard
          const fees = Array.isArray(data) ? data : (data.items || [])
          setInvoices(fees.filter(f => f.status !== 'paid'))
          setSelectedInvoice(null)
          setSuccessMsg('')
          setErrorMsg('')
        })
        .finally(() => setLoadingInvoices(false))
    } else {
      setInvoices([])
    }
  }, [selectedStudent])

  const filteredStudents = useMemo(() => {
    if (!searchQuery) return []
    const q = searchQuery.toLowerCase()
    return students.filter(s => 
      s.user?.full_name?.toLowerCase().includes(q) || 
      s.student_id?.toLowerCase().includes(q)
    ).slice(0, 5)
  }, [students, searchQuery])

  const handleSelectInvoice = (inv) => {
    setSelectedInvoice(inv)
    setPayAmount(inv.balance || inv.amount)
    setSuccessMsg('')
    setErrorMsg('')
  }

  const handlePayment = async (e) => {
    e.preventDefault()
    if (!selectedInvoice || !payAmount) return
    
    setPaymentLoading(true)
    setErrorMsg('')
    setSuccessMsg('')
    
    try {
      await api.post('/api/finance/payments', {
        student_fee_id: selectedInvoice.id,
        amount: parseFloat(payAmount),
        payment_date: new Date().toISOString().split('T')[0],
        payment_method: payMethod,
        transaction_reference: payRef || null,
        status: 'success'
      })
      
      setSuccessMsg(`Payment of ₹${payAmount} recorded successfully!`)
      setSelectedInvoice(null)
      
      // Refresh invoices
      const data = await api.get(`/api/finance/student-fees?student_id=${selectedStudent.id}`)
      const fees = Array.isArray(data) ? data : (data.items || [])
      setInvoices(fees.filter(f => f.status !== 'paid'))
      
    } catch (err) {
      setErrorMsg(err.message || 'Payment failed')
    } finally {
      setPaymentLoading(false)
    }
  }

  return (
    <>
      <PageHeader 
        eyebrow="FINANCE" 
        title="Point of Sale" 
        description="Search students and collect fee payments instantly."
      />
      
      <div className="pos-layout">
        {/* LEFT COLUMN: Student Search & Info */}
        <section className="pos-left">
          <div className="pos-panel search-panel">
            <h3>Find Student</h3>
            <div className="pos-search-box">
              <Search size={18} />
              <input 
                type="text" 
                placeholder="Search by name or ID..." 
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  if (!e.target.value) setSelectedStudent(null)
                }}
              />
            </div>
            
            {filteredStudents.length > 0 && !selectedStudent && (
              <div className="pos-search-results">
                {filteredStudents.map(student => (
                  <button 
                    key={student.id} 
                    className="pos-student-result"
                    onClick={() => {
                      setSelectedStudent(student)
                      setSearchQuery(student.user?.full_name)
                    }}
                  >
                    <div className="pos-student-avatar">
                      {student.user?.full_name?.charAt(0)}
                    </div>
                    <div>
                      <strong>{student.user?.full_name}</strong>
                      <small>{student.student_id} • {student.course?.name}</small>
                    </div>
                  </button>
                ))}
              </div>
            )}
            
            {selectedStudent && (
              <div className="pos-student-card">
                <div className="pos-student-header">
                  <UserRound size={40} className="muted-icon" />
                  <div>
                    <h2>{selectedStudent.user?.full_name}</h2>
                    <p>{selectedStudent.student_id}</p>
                  </div>
                </div>
                <div className="pos-student-details">
                  <div><span>Course</span><strong>{selectedStudent.course?.name || 'N/A'}</strong></div>
                  <div><span>Branch</span><strong>{selectedStudent.branch?.name || 'N/A'}</strong></div>
                  <div><span>Semester</span><strong>Semester {selectedStudent.current_semester}</strong></div>
                  <div><span>Status</span><strong className="status-chip active">Active</strong></div>
                </div>
                <button className="pos-clear-btn" onClick={() => {
                  setSelectedStudent(null)
                  setSearchQuery('')
                }}>
                  Change Student
                </button>
              </div>
            )}
          </div>
        </section>

        {/* RIGHT COLUMN: Invoices & Payment */}
        <section className="pos-right">
          {!selectedStudent ? (
            <div className="pos-empty-state">
              <WalletCards size={48} />
              <h3>No Student Selected</h3>
              <p>Search and select a student to view their pending fee invoices.</p>
            </div>
          ) : (
            <div className="pos-panel billing-panel">
              <div className="pos-billing-header">
                <h3>Pending Invoices</h3>
                <span className="badge">{invoices.length} Due</span>
              </div>
              
              {loadingInvoices ? (
                <div className="pos-loading">Loading invoices...</div>
              ) : invoices.length === 0 ? (
                <div className="pos-success-state">
                  <CheckCircle2 size={32} />
                  <p>All clear! No pending dues for this student.</p>
                </div>
              ) : (
                <div className="pos-invoices-list">
                  {invoices.map(inv => (
                    <div 
                      key={inv.id} 
                      className={`pos-invoice-item ${selectedInvoice?.id === inv.id ? 'selected' : ''}`}
                      onClick={() => handleSelectInvoice(inv)}
                    >
                      <div className="pos-invoice-icon"><ReceiptIndianRupee size={20} /></div>
                      <div className="pos-invoice-info">
                        <strong>{inv.title}</strong>
                        <small>Due: {inv.due_date || 'N/A'}</small>
                      </div>
                      <div className="pos-invoice-amount">
                        <strong>₹{(inv.balance || inv.amount).toLocaleString()}</strong>
                        <span className={`status-badge ${inv.status}`}>{inv.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Payment Terminal */}
              {selectedInvoice && (
                <div className="pos-payment-terminal">
                  <h4>Record Payment</h4>
                  {successMsg && <div className="pos-alert success"><CheckCircle2 size={16}/> {successMsg}</div>}
                  {errorMsg && <div className="pos-alert error"><AlertCircle size={16}/> {errorMsg}</div>}
                  
                  <form onSubmit={handlePayment} className="pos-payment-form">
                    <div className="pos-form-row">
                      <div className="pos-form-group">
                        <label>Amount (₹)</label>
                        <div className="input-with-icon">
                          <IndianRupee size={16} />
                          <input 
                            type="number" 
                            min="1"
                            step="0.01"
                            max={selectedInvoice.balance || selectedInvoice.amount}
                            value={payAmount}
                            onChange={e => setPayAmount(e.target.value)}
                            required
                          />
                        </div>
                      </div>
                      <div className="pos-form-group">
                        <label>Payment Method</label>
                        <select value={payMethod} onChange={e => setPayMethod(e.target.value)}>
                          <option value="cash">Cash</option>
                          <option value="online">Online / UPI</option>
                          <option value="cheque">Cheque</option>
                          <option value="bank_transfer">Bank Transfer</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="pos-form-group">
                      <label>Reference Number (Optional)</label>
                      <input 
                        type="text" 
                        placeholder="Txn ID, Cheque No, etc."
                        value={payRef}
                        onChange={e => setPayRef(e.target.value)}
                      />
                    </div>
                    
                    <button type="submit" className="pos-pay-btn" disabled={paymentLoading}>
                      {paymentLoading ? 'Processing...' : `Pay ₹${Number(payAmount).toLocaleString()}`}
                    </button>
                  </form>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  )
}
