export type Profile = 'medico' | 'admin' | 'pesquisador'

export type Gender = 'masculino' | 'feminino' | 'outro' | 'nao_informado'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  gender: Gender
  birth_date: string | null
  profile: Profile
}

export interface AuthTokens {
  access: string
  refresh: string
}

export type RegisterResponse = AuthTokens & Pick<User, 'id' | 'email' | 'profile'>

/** Dados retornados ao validar um token de convite. */
export interface InvitationInfo {
  email: string
  profile: Profile
}

export interface ApiErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, string | string[]>
  }
}
