import { useEffect, useState } from 'react'
import { ArrowRight, Check, Eye, EyeOff, LoaderCircle, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../state/AuthContext'

const yearCode = String(new Date().getFullYear()).slice(-2)
const demos = [
  ['Administrator', 'admin@cms.edu'], ['HOD', 'faculty1@cms.edu'],
  ['Faculty', 'faculty2@cms.edu'], ['Student', `aarav.${yearCode}btcs001@cms.edu`],
  ['Accountant', 'accountant.demo@cms.edu'], ['Librarian', 'librarian.demo@cms.edu'],
]

export default function LoginPage() {
  const { login } = useAuth()
  const [captcha, setCaptcha] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  const [form, setForm] = useState({ email: '', password: '', captcha_answer: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const refreshCaptcha = async () => {
    const challenge = await api.get('/captcha/new')
    setCaptcha(challenge)
    setForm((current) => ({ ...current, captcha_answer: '' }))
  }
  useEffect(() => { refreshCaptcha().catch(() => setError('Could not load the security check.')) }, [])

  const submit = async (event) => {
    event.preventDefault(); setError(''); setSubmitting(true)
    try {
      await login({ ...form, captcha_token: captcha.captcha_token })
    } catch (err) {
      setError(err.message); refreshCaptcha().catch(() => {})
    } finally { setSubmitting(false) }
  }

  return <main className="login-page">
    <section className="login-story">
      <div className="story-orb orb-one" /><div className="story-orb orb-two" />
      <div className="story-brand"><span><Sparkles size={18} /></span> EduCore</div>
      <div className="story-content">
        <p className="eyebrow light">ONE CAMPUS. ONE PULSE.</p>
        <h1>Every campus decision,<br /><em>beautifully connected.</em></h1>
        <p>Bring academics, people and operations together in a calm workspace built for meaningful progress.</p>
        <div className="story-points">
          <span><Check size={15} /> Role-aware workspaces</span>
          <span><Check size={15} /> Live academic operations</span>
          <span><Check size={15} /> Protected campus data</span>
        </div>
      </div>
      <div className="story-trust"><ShieldCheck size={18} /><span><strong>Enterprise ready</strong><small>Secure access · Audited actions</small></span></div>
    </section>

    <section className="login-panel">
      <form className="login-form" onSubmit={submit}>
        <div className="login-heading"><p className="eyebrow">WELCOME BACK</p><h2>Sign in to your workspace</h2><p>Use your institutional account to continue.</p></div>
        {error && <div className="form-error">{error}</div>}
        <label className="field"><span>Email address</span><input type="email" required autoComplete="username" placeholder="you@cms.edu" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <label className="field"><span>Password</span><div className="password-field"><input type={showPassword ? 'text' : 'password'} required autoComplete="current-password" placeholder="Enter your password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /><button type="button" onClick={() => setShowPassword((show) => !show)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
        <div className="captcha-row">
          <label className="field"><span>Security check</span><input required placeholder="Enter the code" value={form.captcha_answer} onChange={(e) => setForm({ ...form, captcha_answer: e.target.value })} /></label>
          <div className="captcha-box">{captcha ? <img src={captcha.image_url} alt="Security code" /> : <LoaderCircle className="spin" />}<button type="button" onClick={refreshCaptcha} aria-label="New security code"><RefreshCw size={15} /></button></div>
        </div>
        <button className="primary-button login-submit" disabled={submitting || !captcha}>{submitting ? <LoaderCircle className="spin" size={18} /> : <>Enter workspace <ArrowRight size={18} /></>}</button>
        <div className="demo-access"><div><span>Demo access</span><small>Seeded accounts use the administrator password.</small></div><div className="demo-chips">{demos.map(([label, email]) => <button type="button" key={email} onClick={() => setForm({ ...form, email })}>{label}</button>)}</div></div>
      </form>
      <p className="login-footer">© 2026 EduCore · Campus operations, thoughtfully designed.</p>
    </section>
  </main>
}
