import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { AxiosError } from 'axios'
import api from '@/lib/api/client'
import { useAuth } from '../AuthContext'
import { registerSchema, type RegisterInput } from '../schemas'
import type { ApiErrorResponse, Gender, InvitationInfo, Profile } from '../types'

const PROFILE_LABELS: Record<Profile, string> = {
  medico: 'Médico',
  admin: 'Administrador',
  pesquisador: 'Pesquisador',
}

const GENDERS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'masculino', label: 'Masculino' },
  { value: 'feminino', label: 'Feminino' },
  { value: 'outro', label: 'Outro' },
  { value: 'nao_informado', label: 'Prefiro não informar' },
]

function extractError(err: unknown, fallback: string): string {
  if (
    err instanceof AxiosError &&
    err.response?.data &&
    typeof err.response.data === 'object'
  ) {
    const body = err.response.data as ApiErrorResponse
    const details = body.error?.details
    if (details && typeof details === 'object') {
      const messages = Object.entries(details)
        .map(([field, msgs]) => {
          const list = Array.isArray(msgs) ? msgs : [msgs]
          return `${field}: ${list.join(', ')}`
        })
        .join('; ')
      return messages || body.error?.message || fallback
    }
    return body.error?.message ?? fallback
  }
  return fallback
}

export default function InvitePage() {
  const { token = '' } = useParams<{ token: string }>()
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()

  const [invitation, setInvitation] = useState<InvitationInfo | null>(null)
  const [checking, setChecking] = useState(true)
  const [inviteError, setInviteError] = useState('')
  const [serverError, setServerError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: { gender: 'nao_informado' },
  })

  useEffect(() => {
    let active = true
    async function checkInvite() {
      try {
        const { data } = await api.get<InvitationInfo>(`auth/invite/${token}/`)
        if (active) setInvitation(data)
      } catch (err) {
        if (active) {
          setInviteError(
            extractError(err, 'Convite inválido ou expirado.'),
          )
        }
      } finally {
        if (active) setChecking(false)
      }
    }
    void checkInvite()
    return () => {
      active = false
    }
  }, [token])

  const onSubmit = async (data: RegisterInput) => {
    setServerError('')
    try {
      await registerUser(token, data)
      navigate('/dashboard')
    } catch (err) {
      setServerError(extractError(err, 'Erro ao concluir o cadastro.'))
    }
  }

  if (checking) {
    return (
      <div className="auth-container">
        <p>Validando convite…</p>
      </div>
    )
  }

  if (inviteError || !invitation) {
    return (
      <div className="auth-container">
        <h1>Convite inválido</h1>
        <div className="error-message">{inviteError}</div>
        <p className="link-text">
          <Link to="/login">Voltar para o login</Link>
        </p>
      </div>
    )
  }

  return (
    <div className="auth-container">
      <h1>Concluir cadastro</h1>
      <p className="link-text">
        Convite para <strong>{invitation.email}</strong> — perfil{' '}
        <strong>{PROFILE_LABELS[invitation.profile]}</strong>
      </p>
      {serverError && <div className="error-message">{serverError}</div>}
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" value={invitation.email} disabled readOnly />
        </div>
        <div className="form-group">
          <label htmlFor="first_name">Nome</label>
          <input
            id="first_name"
            type="text"
            {...register('first_name')}
            autoComplete="given-name"
          />
          {errors.first_name && (
            <span className="field-error">{errors.first_name.message}</span>
          )}
        </div>
        <div className="form-group">
          <label htmlFor="last_name">Sobrenome</label>
          <input
            id="last_name"
            type="text"
            {...register('last_name')}
            autoComplete="family-name"
          />
          {errors.last_name && (
            <span className="field-error">{errors.last_name.message}</span>
          )}
        </div>
        <div className="form-group">
          <label htmlFor="gender">Gênero</label>
          <select id="gender" {...register('gender')}>
            {GENDERS.map((g) => (
              <option key={g.value} value={g.value}>
                {g.label}
              </option>
            ))}
          </select>
          {errors.gender && (
            <span className="field-error">{errors.gender.message}</span>
          )}
        </div>
        <div className="form-group">
          <label htmlFor="birth_date">Data de nascimento</label>
          <input id="birth_date" type="date" {...register('birth_date')} />
          {errors.birth_date && (
            <span className="field-error">{errors.birth_date.message}</span>
          )}
        </div>
        <div className="form-group">
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            {...register('password')}
            autoComplete="new-password"
          />
          {errors.password && (
            <span className="field-error">{errors.password.message}</span>
          )}
        </div>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Cadastrando…' : 'Cadastrar'}
        </button>
      </form>
      <p className="link-text">
        Já tem conta? <Link to="/login">Entrar</Link>
      </p>
    </div>
  )
}
