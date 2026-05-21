import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import api from '@/lib/api/client'
import type { RegisterInput } from './schemas'
import type { AuthTokens, RegisterResponse, User } from './types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<AuthTokens>
  register: (token: string, data: RegisterInput) => Promise<RegisterResponse>
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

  const login = async (email: string, password: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens>('auth/login/', { email, password })
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
    token: string,
    data: RegisterInput,
  ): Promise<RegisterResponse> => {
    const { data: result } = await api.post<RegisterResponse>('auth/register/', {
      token,
      ...data,
    })
    if (result.access && result.refresh) {
      localStorage.setItem('access_token', result.access)
      localStorage.setItem('refresh_token', result.refresh)
      try {
        const { data: userData } = await api.get<User>('auth/user/')
        setUser(userData)
      } catch {
        // Same fallback as login: registration succeeded but profile fetch failed.
      }
    }
    return result
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
