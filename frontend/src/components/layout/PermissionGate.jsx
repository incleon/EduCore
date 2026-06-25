import { ShieldAlert } from 'lucide-react'
import { useAuth } from '../../state/AuthContext'

/**
 * PermissionGate — Route-level authorization guard.
 *
 * Wraps a page component and checks whether the current user satisfies the
 * required permission *or* a custom predicate (e.g. `user.is_hod`).
 * If the check fails the user sees an "Access Denied" card with a link
 * back to the dashboard.
 *
 * Props:
 *   permission  – permission string checked via `can()`
 *   check       – optional custom predicate `(user) => boolean`
 *   children    – the protected page content
 */
export default function PermissionGate({ permission, check, children }) {
  const { user, can } = useAuth()

  const allowed = permission ? can(permission) : true
  const customAllowed = check ? check(user) : true

  if (allowed && customAllowed) return children

  return (
    <div className="access-denied-card">
      <div className="access-denied-icon"><ShieldAlert size={40} strokeWidth={1.5} /></div>
      <h2>Access Denied</h2>
      <p>You do not have the required permissions to view this page.</p>
      <a href="/dashboard" className="access-denied-link">← Return to Dashboard</a>
    </div>
  )
}
