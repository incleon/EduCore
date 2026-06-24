import { LoaderCircle, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { getValue } from '../../config/resources'
import { api } from '../../lib/api'

const optionKey = (field) => field.options?.endpoint

export default function RecordFormModal({ resource, record, mode, onClose, onSaved }) {
  const fields = resource[mode]
  const [form, setForm] = useState({})
  const [optionData, setOptionData] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const optionSources = useMemo(() => [...new Map(fields.filter((item) => item.options).map((item) => [optionKey(item), item.options])).values()], [fields])

  useEffect(() => {
    const initial = {}
    fields.forEach((item) => {
      const value = mode === 'edit' ? getValue(record, item.source || item.name) : item.defaultValue
      initial[item.name] = value ?? ''
    })
    setForm(initial)
    Promise.all(optionSources.map(async (source) => {
      const response = await api.get(source.endpoint)
      return [source.endpoint, Array.isArray(response) ? response : response?.items || []]
    })).then((entries) => setOptionData(Object.fromEntries(entries))).catch((err) => setError(err.message))
  }, [fields, mode, optionSources, record])

  const change = (name, value) => setForm((current) => {
    const next = { ...current, [name]: value }
    fields.forEach((field) => {
      if (field.options?.filterBy?.some((rule) => rule.form === name)) next[field.name] = ''
    })
    return next
  })

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError('')
    const payload = {}
    fields.forEach((item) => {
      if (item.readOnly) return
      
      const value = form[item.name]
      if ((item.type === 'number' || item.type === 'select') && value === '') {
        if (item.required) payload[item.name] = value
        return
      }
      payload[item.name] = item.type === 'number' ? Number(value) : item.type === 'boolean' ? value === true || value === 'true' : value
    })

    try {
      if (mode === 'create') await api.post(resource.endpoint, payload)
      else await api.put(`${resource.endpoint}/${record.id}`, payload)
      onSaved(`${capitalize(resource.noun)} ${mode === 'create' ? 'created' : 'updated'} successfully.`)
    } catch (err) {
      setError(err.message)
    } finally { setSaving(false) }
  }

  return (
    <div className="modal-backdrop modern" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="form-modal modern" role="dialog" aria-modal="true" aria-labelledby="record-form-title">
        <header className="modern-header">
          <div>
            <p className="eyebrow">{mode === 'create' ? 'NEW RECORD' : 'EDIT RECORD'}</p>
            <h2 id="record-form-title">{mode === 'create' ? `Add ${resource.noun}` : `Modify ${resource.noun}`}</h2>
          </div>
          <button type="button" className="icon-button close-btn" onClick={onClose} aria-label="Close form">
            <X size={20} />
          </button>
        </header>
        
        <form onSubmit={submit}>
          <div className="modal-form-grid modern">
            {fields.map((item) => (
              <div className={`enterprise-field ${item.wide ? 'wide' : ''} ${item.type}`} key={item.name}>
                <label htmlFor={`field-${item.name}`}>
                  {item.label} {item.required && <span className="req">*</span>}
                </label>
                {renderField(item, form[item.name] ?? '', change, optionData, form)}
              </div>
            ))}
          </div>
          
          {error && <div className="form-error modal-error modern">{error}</div>}
          
          <footer className="modern-footer">
            <button type="button" className="secondary-button modern" onClick={onClose}>Cancel</button>
            <button className="primary-button modern" disabled={saving}>
              {saving ? <><LoaderCircle className="spin" size={16} /> Saving</> : mode === 'create' ? `Add ${resource.noun}` : 'Save changes'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}

function renderField(item, value, change, optionData, form) {
  const common = { 
    id: `field-${item.name}`, 
    name: item.name, 
    value, 
    required: item.required, 
    onChange: (event) => change(item.name, event.target.value),
    readOnly: item.readOnly,
    disabled: item.disabled,
    placeholder: item.placeholder || " ", // crucial for floating label trick
    className: 'modern-input'
  }
  
  if (item.type === 'textarea') return <textarea {...common} rows="3" />
  
  if (item.type === 'boolean') {
    return (
      <select {...common}>
        <option value="true">Yes</option>
        <option value="false">No</option>
      </select>
    )
  }
  
  if (item.type === 'select') {
    const records = item.options ? (optionData[item.options.endpoint] || []).filter((record) =>
      (item.options.filterBy || []).every((rule) => {
        const selected = form[rule.form]
        if (!selected) return true
        const recordValue = getValue(record, rule.record)
        return rule.optional && (recordValue === null || recordValue === undefined) ? true : String(recordValue) === String(selected)
      })
    ) : []
    return (
      <select {...common}>
        <option value="">{item.required ? `Select ${item.label.toLowerCase()}` : 'None'}</option>
        {item.choices?.map((choice) => <option key={choice} value={choice}>{capitalize(choice)}</option>)}
        {records.map((record) => (
          <option key={getValue(record, item.options.value)} value={getValue(record, item.options.value)}>
            {getValue(record, item.options.label) || getValue(record, item.options.fallback) || `#${record.id}`}
          </option>
        ))}
      </select>
    )
  }
  
  return <input {...common} type={item.type} min={item.min} max={item.max} step={item.step} minLength={item.minLength} />
}

function capitalize(value = '') { return value.charAt(0).toUpperCase() + value.slice(1).replaceAll('_', ' ') }
