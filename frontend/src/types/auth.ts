export type Profile = 'medico' | 'admin' | 'pesquisador'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  profile: Profile
}

export interface AuthTokens {
  access: string
  refresh: string
}

export type RegisterResponse = AuthTokens & Pick<User, 'id' | 'username' | 'email' | 'profile'>

export interface ApiErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, string | string[]>
  }
}
