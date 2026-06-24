import { AlertTriangle, LoaderCircle, X } from 'lucide-react'
import { useState } from 'react'

export default function ConfirmDialog({ title, message, confirmLabel = 'Delete record', onCancel, onConfirm }) {
  const [working, setWorking] = useState(false)
  const confirm = async () => { setWorking(true); await onConfirm(); setWorking(false) }
  return <div className="modal-backdrop" role="presentation"><section className="confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title"><button className="icon-button confirm-close" onClick={onCancel} aria-label="Close confirmation"><X size={18} /></button><span className="danger-icon"><AlertTriangle size={21} /></span><h2 id="confirm-title">{title}</h2><p>{message}</p><footer><button className="secondary-button" onClick={onCancel}>Cancel</button><button className="danger-button" onClick={confirm} disabled={working}>{working ? <LoaderCircle className="spin" size={16} /> : confirmLabel}</button></footer></section></div>
}
