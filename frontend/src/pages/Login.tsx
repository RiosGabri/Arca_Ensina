import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AxiosError } from 'axios'
import { useAuth } from '../context/AuthContext'
import type { ApiErrorResponse } from '../types/auth'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await login(username, password)
      navigate('/dashboard')
    } catch (err) {
      let detail = 'Credenciais inválidas. Tente novamente.'
      if (err instanceof AxiosError) {
        const data = err.response?.data as ApiErrorResponse | undefined
        detail = data?.error?.message ?? detail
      }
      setError(detail)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-container">
      <h1>Entrar</h1>
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
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
      <p className="link-text">
        Não tem conta? <Link to="/register">Cadastre-se</Link>
      </p>
    </div>
  )
}
