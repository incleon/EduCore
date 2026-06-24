import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './state/AuthContext'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
import { resourceConfigs } from './config/resources'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ResourcePage = lazy(() => import('./pages/ResourcePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const TimetablePage = lazy(() => import('./pages/TimetablePage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const AttendancePage = lazy(() => import('./pages/AttendancePage'))
const AssignmentsPage = lazy(() => import('./pages/AssignmentsPage'))

function ProtectedApp() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />

  return (
    <AppShell>
      <Suspense fallback={<div className="content-loader">Loading workspace</div>}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        {resourceConfigs.map((config) => (
          <Route key={config.slug} path={`/${config.slug}`} element={config.slug === 'attendance' ? <AttendancePage /> : <ResourcePage config={config} />} />
        ))}
        <Route path="/assignments" element={<AssignmentsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/timetable" element={<TimetablePage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
