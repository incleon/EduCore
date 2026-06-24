import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/auth/me').then(setUser).catch(() => setUser(null)).finally(() => setLoading(false))
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    login: async (credentials) => {
      await api.post('/auth/login', credentials)
      const currentUser = await api.get('/auth/me')
      setUser(currentUser)
    },
    logout: async () => {
      await api.post('/auth/logout', {})
      setUser(null)
    },
    can: (permission) => !permission || user?.permissions?.includes(permission),
  }), [user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
