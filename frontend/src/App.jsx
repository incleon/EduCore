import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './state/AuthContext'
import AppShell from './components/layout/AppShell'
import PermissionGate from './components/layout/PermissionGate'
import LoginPage from './pages/LoginPage'
import { resourceConfigs } from './config/resources'
import { canAccessAssignments, canAccessResourceForRole, canAccessTimetable } from './config/roleAccess'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const HodPanelPage = lazy(() => import('./pages/HodPanelPage'))
const HodManagementPage = lazy(() => import('./pages/HodManagementPage'))
const ResourcePage = lazy(() => import('./pages/ResourcePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const TimetablePage = lazy(() => import('./pages/TimetablePage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const AttendancePage = lazy(() => import('./pages/AttendancePage'))
const AssignmentsPage = lazy(() => import('./pages/AssignmentsPage'))
const FeeCollectionPage = lazy(() => import('./pages/FeeCollectionPage'))

function ProtectedApp() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />

  // HOD users (who are not also admins) only see their own branch data
  const isHodOnly = user?.is_hod && !user?.roles?.includes('admin')
  const hodFilters = isHodOnly ? { branch_id: user.hod_branch_ids?.[0] } : {}

  return (
    <AppShell>
      <Suspense fallback={<div className="content-loader">Loading workspace</div>}>
      <Routes>
        <Route path="/" element={<Navigate to={user?.is_hod ? "/hod-panel" : "/dashboard"} replace />} />
        <Route path="/dashboard" element={user?.is_hod ? <Navigate to="/hod-panel" replace /> : <DashboardPage />} />
        <Route path="/hod-panel" element={<PermissionGate check={(u) => u?.is_hod}><HodPanelPage /></PermissionGate>} />
        <Route path="/hod-management" element={<PermissionGate permission="manage_academic_structure"><HodManagementPage /></PermissionGate>} />
        {resourceConfigs.map((config) => (
          <Route key={config.slug} path={`/${config.slug}`} element={
            <PermissionGate permission={config.permission} check={(u) => canAccessResourceForRole(u, config.slug)}>
              {config.slug === 'attendance' ? <AttendancePage forcedFilters={hodFilters} /> : 
               config.slug === 'fee-collection' ? <FeeCollectionPage /> : 
               <ResourcePage config={config} forcedFilters={hodFilters} />}
            </PermissionGate>
          } />
        ))}
        <Route path="/assignments" element={<PermissionGate check={canAccessAssignments}><AssignmentsPage /></PermissionGate>} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/timetable" element={<PermissionGate check={canAccessTimetable}><TimetablePage /></PermissionGate>} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="*" element={<Navigate to={user?.is_hod ? "/hod-panel" : "/dashboard"} replace />} />
      </Routes>
      </Suspense>
    </AppShell>
  )
}

export default function App() {
  const { user, loading } = useAuth()
  if (loading) return <div className="app-loader"><span /><p>Preparing your workspace</p></div>

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/*" element={<ProtectedApp />} />
    </Routes>
  )
}
