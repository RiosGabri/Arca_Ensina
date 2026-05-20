import { useNavigate, Link } from 'react-router'
import { Bell, LogOut, Plus, ArrowRight } from 'lucide-react'
import { useAuth } from '@/features/auth'
import { usePatients } from '@/features/patient/api'
import PatientPill from '@/features/patient/components/PatientPill'
import { cn } from '@/lib/utils'

const WEEKDAYS = [
  'DOMINGO',
  'SEGUNDA-FEIRA',
  'TERÇA-FEIRA',
  'QUARTA-FEIRA',
  'QUINTA-FEIRA',
  'SEXTA-FEIRA',
  'SÁBADO',
] as const

const MONTHS = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
] as const

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Bom Dia'
  if (h < 18) return 'Boa Tarde'
  return 'Boa Noite'
}

function getDisplayName(user: { first_name: string; last_name: string; username: string; profile: string }): string {
  const firstName = user.first_name || user.username
  if (user.profile === 'medico') return `Dr. ${firstName}`
  return firstName
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { data: patients = [], isLoading } = usePatients()

  const now = new Date()
  const weekday = WEEKDAYS[now.getDay()]
  const dateStr = `${now.getDate()} de ${MONTHS[now.getMonth()]}`

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex w-full flex-col gap-6 px-5 tablet:gap-10 tablet:px-10">
      {/* ── Greeting + actions row ── */}
      <header className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-caption font-medium tracking-widest text-muted-foreground tablet:text-body-md">
            {weekday}
          </span>
          <h1 className="text-display-sm leading-tight tablet:text-display-lg">
            {getGreeting()},
            <br />
            <span className="text-primary">
              {user ? getDisplayName(user) : ''}
            </span>
          </h1>
          <p className="mt-1 text-body-md text-muted-foreground tablet:text-body-lg">
            {dateStr}
            <span className="mx-1.5">•</span>
            {isLoading ? '…' : `${patients.length} ${patients.length === 1 ? 'paciente ativo' : 'pacientes ativos'}`}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2 pt-4 tablet:gap-3 tablet:pt-6">
          <button
            type="button"
            className="flex size-11 items-center justify-center rounded-full border border-border bg-background transition-colors hover:bg-muted tablet:size-12"
            aria-label="Notificações"
          >
            <Bell size={20} className="text-foreground" />
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="flex size-11 items-center justify-center rounded-full border border-border bg-background transition-colors hover:bg-muted tablet:size-12"
            aria-label="Sair"
          >
            <LogOut size={18} className="text-muted-foreground" />
          </button>
        </div>
      </header>

      {/* ── Patients row ── */}
      <section>
        <div className="mb-3 flex items-center justify-between tablet:mb-5">
          <span className="text-caption font-medium tracking-widest text-muted-foreground tablet:text-body-md">
            PACIENTES
          </span>
          <Link
            to="/patients/list"
            className="inline-flex items-center gap-1 text-body-md font-medium text-primary transition-colors hover:text-primary/80 tablet:text-body-lg"
          >
            Ver todos
            <ArrowRight size={14} className="tablet:size-4" />
          </Link>
        </div>

        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-none tablet:gap-4">
          {/* Add patient pill */}
          <button
            type="button"
            onClick={() => navigate('/patients')}
            className={cn(
              'inline-flex min-w-36 max-w-48 shrink-0 flex-col items-center justify-center gap-1 rounded-2xl border border-dashed border-border px-3.5 py-3',
              'cursor-pointer transition-all hover:border-primary hover:bg-arca-blue-50',
              'outline-none focus-visible:ring-3 focus-visible:ring-ring/30',
              'tablet:min-w-44 tablet:max-w-56 tablet:px-5 tablet:py-4',
            )}
          >
            <span className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary tablet:size-9">
              <Plus size={16} className="tablet:size-5" />
            </span>
            <span className="text-caption font-medium text-muted-foreground tablet:text-body-md">
              Adicionar
            </span>
          </button>

          {/* Patient pills */}
          {isLoading
            ? Array.from({ length: 2 }).map((_, i) => (
                <div
                  key={i}
                  className="min-w-36 max-w-48 shrink-0 animate-pulse rounded-2xl border border-border bg-muted px-3.5 py-3 tablet:min-w-44 tablet:max-w-56 tablet:px-5 tablet:py-4"
                >
                  <div className="mb-1.5 h-4 w-24 rounded bg-neutral-300 tablet:h-5 tablet:w-28" />
                  <div className="h-3 w-16 rounded bg-neutral-200 tablet:h-4 tablet:w-20" />
                </div>
              ))
            : patients.map((patient) => (
                <div key={patient.id} className="shrink-0">
                  <div className="tablet:hidden">
                    <PatientPill patient={patient} />
                  </div>
                  <div className="hidden tablet:block">
                    <PatientPill patient={patient} size="lg" />
                  </div>
                </div>
              ))}
        </div>
      </section>
    </div>
  )
}
