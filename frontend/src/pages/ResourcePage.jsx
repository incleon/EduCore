import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, ChevronLeft, ChevronRight, Download, LoaderCircle, Pencil, Plus, Search, SlidersHorizontal, Trash2, X } from 'lucide-react'
import { api } from '../lib/api'
import { getValue } from '../config/resources'
import { resourceForms } from '../config/resourceForms'
import { useAuth } from '../state/AuthContext'
import PageHeader from '../components/ui/PageHeader'
import RecordFormModal from '../components/ui/RecordFormModal'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import ProfileDetailModal from '../components/ui/ProfileDetailModal'
import PeopleDirectory from '../components/ui/PeopleDirectory'
import '../styles/people-directory.css'

const searchableResources = ['students', 'teachers', 'departments', 'courses', 'subjects', 'library']
const EMPTY_FILTERS = {}
const hierarchyResources = new Set(['students', 'teachers', 'courses', 'branches', 'curricula', 'sections', 'subjects', 'curriculum-subjects', 'elective-groups', 'faculty-assignments', 'attendance', 'marks'])
const humanize = (value) => String(value ?? '').replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase())
const display = (value, path) => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (path.includes('amount') && !Number.isNaN(Number(value))) return `₹${Number(value).toLocaleString('en-IN')}`
  return humanize(value)
}

export default function ResourcePage({ config, forcedFilters = EMPTY_FILTERS }) {
  const { can } = useAuth()
  const formConfig = resourceForms[config.slug]
  const canManage = Boolean(formConfig && can(formConfig.permission))
  const [records, setRecords] = useState([])
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 10 })
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortOrder, setSortOrder] = useState('default')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editor, setEditor] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [deletingAll, setDeletingAll] = useState(false)
  const [toast, setToast] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [viewing, setViewing] = useState(null)
  const [hierarchy, setHierarchy] = useState({ department_id: '', course_id: '', branch_id: '' })
  const [hierarchyOptions, setHierarchyOptions] = useState({ departments: [], courses: [], branches: [] })
  const profileResource = ['students', 'teachers'].includes(config.slug)
  const hierarchyResource = hierarchyResources.has(config.slug)

  useEffect(() => {
    if (!hierarchyResource) return
    Promise.all([api.get('/api/departments?page=1&page_size=100'), api.get('/api/courses?page=1&page_size=100'), api.get('/api/academic/branches')])
      .then(([departments, courses, branches]) => setHierarchyOptions({ departments: departments.items || [], courses: courses.items || [], branches: branches.items || [] }))
      .catch(() => {})
  }, [hierarchyResource])

  useEffect(() => { const id = setTimeout(() => setDebounced(query), 250); return () => clearTimeout(id) }, [query])
  useEffect(() => {
    if (!can(config.permission)) return
    setLoading(true); setError('')
    const params = new URLSearchParams({ page: String(meta.page), page_size: '10' })
    if (debounced && searchableResources.includes(config.slug)) params.set('search', debounced)
    if (hierarchyResource) Object.entries({ ...hierarchy, ...forcedFilters }).forEach(([key, value]) => value && params.set(key, value))
    api.get(`${config.endpoint}?${params}`).then((payload) => {
      const items = Array.isArray(payload) ? payload : payload?.items || []
      setRecords(items); setMeta((current) => ({ ...current, total: payload?.total ?? items.length, page_size: payload?.page_size ?? 10 }))
    }).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [config, debounced, meta.page, can, reloadKey, hierarchy, hierarchyResource, forcedFilters])

  const filtered = useMemo(() => records.filter((record) => {
    const localSearch = debounced && !searchableResources.includes(config.slug)
      ? JSON.stringify(record).toLowerCase().includes(debounced.toLowerCase()) : true
    const statusMatch = statusFilter ? String(record.status?.value || record.status || '').toLowerCase() === statusFilter : true
    return localSearch && statusMatch
  }).sort((left, right) => {
    if (sortOrder === 'default') return 0
    const path = config.columns[1]?.[0] || config.columns[0][0]
    const comparison = String(getValue(left, path) || '').localeCompare(String(getValue(right, path) || ''))
    return sortOrder === 'az' ? comparison : -comparison
  }), [records, debounced, config, statusFilter, sortOrder])
  const statuses = useMemo(() => [...new Set(records.map((record) => String(record.status?.value || record.status || '').toLowerCase()).filter(Boolean))], [records])
  const pageCount = Math.max(1, Math.ceil(meta.total / meta.page_size))
  const hasActions = canManage || profileResource
  const columnCount = config.columns.length + (hasActions ? 1 : 0)
  const hierarchyCourses = hierarchyOptions.courses.filter((item) => !hierarchy.department_id || String(item.department_id) === String(hierarchy.department_id))
  const hierarchyBranches = hierarchyOptions.branches.filter((item) => !hierarchy.course_id || String(item.course_id) === String(hierarchy.course_id))

  const refresh = (message) => {
    setEditor(null); setDeleting(null); setDeletingAll(false); setToast(message); setReloadKey((key) => key + 1)
    setTimeout(() => setToast(''), 3500)
  }

  const remove = async () => {
    try {
      await api.delete(`${config.endpoint}/${deleting.id}`)
      refresh(`${humanize(formConfig.noun)} deleted successfully.`)
    } catch (err) {
      setDeleting(null); setError(err.message)
    }
  }

  const removeAll = async () => {
    try {
      await api.delete(`${config.endpoint}/all`)
      refresh(`All ${config.label} deleted successfully.`)
    } catch (err) {
      setDeletingAll(false); setError(err.message)
    }
  }

  const exportCsv = () => {
    const headings = config.columns.map(([, label]) => label)
    const rows = filtered.map((record) => config.columns.map(([path]) => getValue(record, path)))
    const escape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`
    const csv = [headings, ...rows].map((row) => row.map(escape).join(',')).join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = `${config.slug}.csv`; link.click(); URL.revokeObjectURL(url)
    setToast('CSV export downloaded.')
  }

  if (!can(config.permission)) return <div className="not-allowed"><config.icon size={24} /><h2>This workspace is not assigned to your role.</h2><p>Ask an administrator if you believe you need access.</p></div>

  return <>
    <PageHeader eyebrow={config.eyebrow.toUpperCase()} title={config.label} description={config.description} actions={<><button className="secondary-button" onClick={exportCsv}><Download size={16} /> Export</button>{canManage && <><button className="secondary-button" style={{color: 'var(--danger)', borderColor: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.5rem'}} onClick={() => setDeletingAll(true)}><Trash2 size={16} /> Delete All</button><button className="primary-button" onClick={() => setEditor({ mode: 'create', record: null })}><Plus size={16} /> Add {formConfig.noun}</button></>}</>} />
    {toast && <div className="toast-message"><CheckCircle2 size={17} />{toast}<button onClick={() => setToast('')} aria-label="Dismiss message"><X size={15} /></button></div>}
    {error && <div className="inline-error">{error}</div>}
    <section className="panel resource-panel">
      <div className="table-toolbar"><label className="table-search"><Search size={17} /><input value={query} onChange={(event) => { setQuery(event.target.value); setMeta((current) => ({ ...current, page: 1 })) }} placeholder={`Search ${config.label.toLowerCase()}…`} /></label><button className={`filter-button ${filtersOpen ? 'active' : ''}`} onClick={() => setFiltersOpen((open) => !open)}><SlidersHorizontal size={16} /> Filters{statusFilter && <i />}</button><span className="record-count">{meta.total.toLocaleString()} records</span></div>
      {filtersOpen && <div className="filter-strip">{hierarchyResource && <><label><span>Department</span><select value={hierarchy.department_id} onChange={(event) => setHierarchy({ department_id: event.target.value, course_id: '', branch_id: '' })}><option value="">All departments</option>{hierarchyOptions.departments.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>{config.slug !== 'courses' && <label><span>Course</span><select value={hierarchy.course_id} onChange={(event) => setHierarchy((current) => ({ ...current, course_id: event.target.value, branch_id: '' }))}><option value="">All courses</option>{hierarchyCourses.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}{config.slug !== 'courses' && config.slug !== 'branches' && <label><span>Branch</span><select value={hierarchy.branch_id} onChange={(event) => setHierarchy((current) => ({ ...current, branch_id: event.target.value }))}><option value="">All branches</option>{hierarchyBranches.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}</>}{statuses.length > 0 && <label><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option>{statuses.map((status) => <option key={status} value={status}>{humanize(status)}</option>)}</select></label>}<label><span>Sort records</span><select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}><option value="default">Newest first</option><option value="az">A to Z</option><option value="za">Z to A</option></select></label><button onClick={() => { setStatusFilter(''); setSortOrder('default'); setQuery(''); setHierarchy({ department_id: '', course_id: '', branch_id: '' }) }}>Reset filters</button></div>}
      {profileResource
        ? <PeopleDirectory
            kind={config.slug}
            records={filtered}
            loading={loading}
            emptyIcon={config.icon}
            canManage={canManage}
            onView={setViewing}
            onEdit={(record) => setEditor({ mode: 'edit', record })}
            onDelete={setDeleting}
          />
        : <div className="table-scroll">
            <table className="data-table"><thead><tr>{config.columns.map(([, label]) => <th key={label}>{label}</th>)}{hasActions && <th className="actions-head">Actions</th>}</tr></thead><tbody>
              {loading ? <tr><td colSpan={columnCount}><div className="table-state"><LoaderCircle className="spin" /> Loading records</div></td></tr>
                : filtered.length ? filtered.map((record, index) => <tr key={record.id ?? index}>{config.columns.map(([path], columnIndex) => { const raw = getValue(record, path); const value = raw?.value ?? raw; const isStatus = path === 'status'; return <td key={path}>{columnIndex === 1 && config.slug !== 'courses' && config.slug !== 'departments' ? <span className="primary-cell">{display(value, path)}</span> : isStatus ? <span className={`status-badge ${String(value).toLowerCase()}`}>{display(value, path)}</span> : display(value, path)}</td> })}{hasActions && <td className="row-actions">{canManage && <><button onClick={() => setEditor({ mode: 'edit', record })} aria-label={`Edit ${formConfig.noun}`} title="Modify"><Pencil size={15} /></button><button className="delete" onClick={() => setDeleting(record)} aria-label={`Delete ${formConfig.noun}`} title="Delete"><Trash2 size={15} /></button></>}</td>}</tr>)
                : <tr><td colSpan={columnCount}><div className="table-state"><config.icon size={24} /><strong>No records found</strong><span>Try adjusting your search or add a new record.</span></div></td></tr>}
            </tbody></table>
          </div>
      }
      <div className="pagination"><p>Page <strong>{meta.page}</strong> of <strong>{pageCount}</strong></p><div><button disabled={meta.page <= 1} onClick={() => setMeta((current) => ({ ...current, page: current.page - 1 }))}><ChevronLeft size={16} /></button><button disabled={meta.page >= pageCount} onClick={() => setMeta((current) => ({ ...current, page: current.page + 1 }))}><ChevronRight size={16} /></button></div></div>
    </section>
    {editor && <RecordFormModal resource={{ ...formConfig, endpoint: config.endpoint }} mode={editor.mode} record={editor.record} onClose={() => setEditor(null)} onSaved={refresh} />}
    {deleting && <ConfirmDialog title={`Delete this ${formConfig.noun}?`} message="This record will be removed from active views. Related records may also be affected." onCancel={() => setDeleting(null)} onConfirm={remove} />}
    {deletingAll && <ConfirmDialog title={`Delete ALL ${config.label}?`} message="WARNING: This action is irreversible. It will delete ALL records in this resource and recursively cascade to all related records." onCancel={() => setDeletingAll(false)} onConfirm={removeAll} />}
    {viewing && <ProfileDetailModal endpoint={config.endpoint} record={viewing} kind={config.slug} onClose={() => setViewing(null)} />}
  </>
}
