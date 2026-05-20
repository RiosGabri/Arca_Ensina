import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { AxiosError } from 'axios'
import { Mail, Lock, Loader2 } from 'lucide-react'
import { useAuth } from '../AuthContext'
import { loginSchema, type LoginInput } from '../schemas'
import type { ApiErrorResponse } from '../types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function LoginPage() {
  const [serverError, setServerError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  })

  const onSubmit = async (data: LoginInput) => {
    setServerError('')
    try {
      await login(data.username, data.password)
      navigate('/dashboard')
    } catch (err) {
      let detail = 'Credenciais inválidas. Tente novamente.'
      if (err instanceof AxiosError) {
        const body = err.response?.data as ApiErrorResponse | undefined
        detail = body?.error?.message ?? detail
      }
      setServerError(detail)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col md:flex-row">
      {/* ── Mobile top banner ── */}
      <div className="relative h-40 overflow-hidden bg-[#0c54b2] md:hidden">
        <div className="absolute -left-20 -top-10 h-72 w-72 rounded-full bg-[#0a4a9e]" />
        <div className="absolute -left-18 -top-4 h-56 w-56 rounded-full bg-[#0e3f88]" />
        <div className="absolute -left-14 top-2 h-42 w-42 rounded-full bg-[#0b3572]" />
        <span className="absolute left-6 top-1/2 -translate-y-1/2 z-10 text-[2.25rem] font-extrabold tracking-wide text-white">
          ARCA
        </span>
      </div>

      {/* ── Left brand panel (desktop) ── */}
      <div className="relative hidden w-[42%] overflow-hidden bg-[#0c54b2] md:block">
        <div className="absolute right-[35%] top-1/2 -translate-y-1/2 h-[130%] aspect-square rounded-full bg-[#0a4a9e]" />
        <div className="absolute right-[45%] top-1/2 -translate-y-1/2 h-full aspect-square rounded-full bg-[#0e3f88]" />
        <div className="absolute right-[57%] top-1/2 -translate-y-1/2 h-[70%] aspect-square rounded-full bg-[#0b3572]" />
        <span className="absolute left-10 top-1/2 -translate-y-1/2 z-10 text-[4rem] font-extrabold tracking-wide text-white">
          ARCA
        </span>
      </div>

      {/* ── Form panel ── */}
      <div className="flex flex-1 flex-col items-center justify-center bg-background px-6 py-12 md:px-16">
        <div className="w-full max-w-sm">
          <h1 className="mb-8 text-center text-heading-lg font-bold text-neutral-800 md:text-display-sm md:text-neutral-600">
            Usuário
          </h1>

          {serverError && (
            <div
              role="alert"
              className="mb-6 rounded-xl border border-arca-red-200 bg-arca-red-50 px-4 py-3 text-body-md text-arca-red-700"
            >
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Email / Username */}
            <div className="space-y-1.5">
              <label htmlFor="username" className="sr-only">
                Email
              </label>
              <div className="relative">
                <Mail
                  className="pointer-events-none absolute left-4 top-1/2 size-4.5 -translate-y-1/2 text-neutral-400"
                  aria-hidden="true"
                />
                <Input
                  id="username"
                  type="text"
                  placeholder="Email"
                  className="h-12 pl-11 text-base"
                  {...register('username')}
                  autoComplete="username"
                  aria-invalid={!!errors.username}
                />
              </div>
              {errors.username && (
                <p className="pl-4 text-caption text-destructive">
                  {errors.username.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="sr-only">
                Senha
              </label>
              <div className="relative">
                <Lock
                  className="pointer-events-none absolute left-4 top-1/2 size-4.5 -translate-y-1/2 text-neutral-400"
                  aria-hidden="true"
                />
                <Input
                  id="password"
                  type="password"
                  placeholder="Senha"
                  className="h-12 pl-11 text-base"
                  {...register('password')}
                  autoComplete="current-password"
                  aria-invalid={!!errors.password}
                />
              </div>
              {errors.password && (
                <p className="pl-4 text-caption text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Submit */}
            <div className="flex justify-center pt-2">
              <Button type="submit" size="lg" disabled={isSubmitting} className="min-w-35">
                {isSubmitting ? (
                  <>
                    <Loader2 className="animate-spin" data-icon="inline-start" />
                    Entrando…
                  </>
                ) : (
                  'Login'
                )}
              </Button>
            </div>
          </form>

          <p className="mt-8 text-center text-body-md text-neutral-400">
            Acesso restrito — cadastro somente por convite.
          </p>
        </div>
      </div>
    </div>
  )
}
