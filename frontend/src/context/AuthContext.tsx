import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import api from '../services/api'
import type { AuthTokens, Profile, RegisterResponse, User } from '../types/auth'

interface AuthContextValue {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<AuthTokens>
  register: (
    username: string,
    email: string,
    password: string,
    profile: Profile,
  ) => Promise<RegisterResponse>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const { data } = await api.get<User>('auth/user/')
      setUser(data)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: hydrate auth from localStorage on mount
    void fetchUser()
  }, [fetchUser])

  const login = async (username: string, password: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens>('auth/login/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    try {
      const { data: userData } = await api.get<User>('auth/user/')
      setUser(userData)
    } catch {
      // Backend /auth/user/ unavailable — keep tokens, leave user empty until next fetch.
    }
    return data
  }

  const register = async (
    username: string,
    email: string,
    password: string,
    profile: Profile,
  ): Promise<RegisterResponse> => {
    const { data } = await api.post<RegisterResponse>('auth/register/', {
      username,
      email,
      password,
      profile,
    })
    if (data.access && data.refresh) {
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      try {
        const { data: userData } = await api.get<User>('auth/user/')
        setUser(userData)
      } catch {
        // Same fallback as login: registration succeeded but profile fetch failed.
      }
    }
    return data
  }

  const logout = async (): Promise<void> => {
    try {
      await api.post('auth/logout/', {
        refresh: localStorage.getItem('refresh_token'),
      })
    } catch {
      // Always clear local state even if blacklist call fails.
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  const isAuthenticated = user !== null

  const value: AuthContextValue = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
