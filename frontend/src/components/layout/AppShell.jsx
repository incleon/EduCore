import { useState } from 'react'
import { Bell, CalendarRange, ChevronDown, Command, LayoutDashboard, LogOut, Menu, Search, UserRound, X } from 'lucide-react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { resourceConfigs } from '../../config/resources'
import {
  canAccessAssignments,
  canAccessResourceForRole,
  canAccessTimetable,
  resourceLabelForRole,
} from '../../config/roleAccess'
import { useAuth } from '../../state/AuthContext'

const initials = (name = '') => name.split(' ').filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()

export default function AppShell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [workspaceQuery, setWorkspaceQuery] = useState('')
  const { user, can, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isLibrarian = user?.roles?.includes('librarian') && !user?.roles?.includes('admin')
  const isAccountant = user?.roles?.includes('accountant') && !user?.roles?.includes('admin')
  const showAssignments = canAccessAssignments(user)
  const showTimetable = canAccessTimetable(user)
  
  const visibleResources = resourceConfigs.filter((item) => {
    if (!can(item.permission)) return false
    if (!canAccessResourceForRole(user, item.slug)) return false
    if (isLibrarian && !(item.slug.startsWith('library') || item.slug === 'book-issues')) return false
    if (isAccountant && item.eyebrow !== 'Finance') return false
    return true
  })

  const searchItems = [
    { label: 'Overview', path: '/dashboard', eyebrow: 'Workspace' },
    ...visibleResources.map((item) => ({ label: resourceLabelForRole(user, item), path: `/${item.slug}`, eyebrow: item.eyebrow })),
    ...(showTimetable ? [
      { label: 'Timetable', path: '/timetable', eyebrow: 'Learning' },
    ] : []),
    ...(showAssignments ? [
      { label: 'Assignments', path: '/assignments', eyebrow: 'Learning' },
    ] : []),
    { label: 'Profile', path: '/profile', eyebrow: 'Account' },
  ].filter((item) => item.label.toLowerCase().includes(workspaceQuery.toLowerCase())).slice(0, 6)

  const leave = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      {mobileOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? 'is-open' : ''}`}>
        <div className="brand-row">
          <div className="brand-mark"><Command size={18} strokeWidth={2.2} /></div>
          <div><strong>EduCore</strong><span>Campus OS</span></div>
          <button className="mobile-close icon-button" onClick={() => setMobileOpen(false)}><X size={18} /></button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          <NavLink to="/dashboard" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={18} /><span>Overview</span>
          </NavLink>
          {user?.is_hod && !isLibrarian && (
            <div className="nav-group">
              <p>HOD Section</p>
              <NavLink to="/hod-panel" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                <LayoutDashboard size={18} /><span>HOD Panel</span>
              </NavLink>
            </div>
          )}
          {['People', 'Academics', 'Learning', 'Operations', 'Finance'].map((group) => {
            const items = visibleResources.filter((item) => item.eyebrow === group)
            if (!items.length && (group !== 'Learning' || isLibrarian || isAccountant)) return null
            return <div className="nav-group" key={group}>
              <p>{group}</p>
              {items.map((item) => {
                const { slug, icon: Icon } = item
                const label = resourceLabelForRole(user, item)
                return (
                <NavLink key={slug} to={`/${slug}`} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                  <Icon size={18} /><span>{label}</span>
                </NavLink>
                )
              })}
              {group === 'People' && can('manage_academic_structure') && !isLibrarian && (
                <NavLink to="/hod-management" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                  <UserRound size={18} /><span>HOD Management</span>
                </NavLink>
              )}
              {group === 'Learning' && showAssignments && (
                <NavLink to="/assignments" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                  <CalendarRange size={18} /><span>Assignments</span>
                </NavLink>
              )}
            </div>
          })}
          {showTimetable && (
            <NavLink to="/timetable" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <CalendarRange size={18} /><span>Timetable</span>
            </NavLink>
          )}
        </nav>

        <div className="sidebar-foot">
          <div className="system-status"><span /><div><strong>All systems normal</strong><small>API connected</small></div></div>
          <p>EduCore v2.0</p>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button className="menu-button icon-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
          <div className="workspace-search"><label className="global-search">
            <Search size={17} />
            <input placeholder="Search your workspace" aria-label="Search workspace" value={workspaceQuery} onChange={(event) => setWorkspaceQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && searchItems[0]) { navigate(searchItems[0].path); setWorkspaceQuery('') } }} />
            <kbd>⌘ K</kbd>
          </label>{workspaceQuery && <div className="search-popover">{searchItems.length ? searchItems.map((item) => <button key={item.path} onClick={() => { navigate(item.path); setWorkspaceQuery('') }}><span>{item.label}</span><small>{item.eyebrow}</small></button>) : <p>No matching workspace</p>}</div>}</div>
          <div className="topbar-actions">
            <button className="icon-button notification-button" aria-label="Notifications" onClick={() => navigate('/notifications')}><Bell size={19} /><span /></button>
            <div className="account-menu">
              <button className="account-trigger" onClick={() => setAccountOpen((open) => !open)}>
                <span className="avatar">{initials(user.full_name)}</span>
                <span className="account-copy">
                  <strong>{user.full_name}</strong>
                  {user?.is_hod
                    ? <small className="hod-badge">HOD, {user.hod_branch_names?.[0] || 'Branch'}</small>
                    : <small>{user.roles?.[0] || 'Member'}</small>}
                </span>
                <ChevronDown size={15} />
              </button>
              {accountOpen && <div className="account-popover">
                <button onClick={() => { navigate('/profile'); setAccountOpen(false) }}><UserRound size={16} /> Profile</button>
                <button className="danger" onClick={leave}><LogOut size={16} /> Sign out</button>
              </div>}
            </div>
          </div>
        </header>
        <section className="page-canvas" key={location.pathname}>{children}</section>
      </main>
    </div>
  )
}
