import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AxiosError } from 'axios'
import { useAuth } from '../context/AuthContext'
import type { ApiErrorResponse, Profile } from '../types/auth'

const PROFILES: ReadonlyArray<{ value: Profile; label: string }> = [
  { value: 'medico', label: 'Médico' },
  { value: 'admin', label: 'Admin' },
  { value: 'pesquisador', label: 'Pesquisador' },
]

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [profile, setProfile] = useState<Profile>('medico')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await register(username, email, password, profile)
      navigate('/dashboard')
    } catch (err) {
      const fallback = 'Erro ao registrar. Tente novamente.'
      if (err instanceof AxiosError && err.response?.data && typeof err.response.data === 'object') {
        const data = err.response.data as ApiErrorResponse
        const details = data.error?.details
        if (details && typeof details === 'object') {
          const messages = Object.entries(details)
            .map(([field, msgs]) => {
              const list = Array.isArray(msgs) ? msgs : [msgs]
              return `${field}: ${list.join(', ')}`
            })
            .join('; ')
          setError(messages || fallback)
        } else {
          setError(data.error?.message ?? fallback)
        }
      } else {
        setError(fallback)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-container">
      <h1>Cadastro</h1>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            autoFocus
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">E-mail</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            minLength={8}
          />
        </div>
        <div className="form-group">
          <label htmlFor="profile">Perfil profissional</label>
          <select
            id="profile"
            value={profile}
            onChange={(e) => setProfile(e.target.value as Profile)}
            required
          >
            {PROFILES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Cadastrando...' : 'Cadastrar'}
        </button>
      </form>
      <p className="link-text">
        Já tem conta? <Link to="/login">Entrar</Link>
      </p>
    </div>
  )
}
