import { Check, UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { usePatients, type Patient } from '@/features/patient'

interface PatientSelectorProps {
  selectedId: string | null
  onSelect: (patient: Patient) => void
}

function PatientSelector({ selectedId, onSelect }: PatientSelectorProps) {
  const navigate = useNavigate()
  const { data: patients = [], isLoading, isError } = usePatients()

  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-32 rounded-3xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <p className="text-body-md text-muted-foreground">
        Não foi possível carregar os pacientes.
      </p>
    )
  }

  if (patients.length === 0) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-body-md text-muted-foreground">
          Nenhum paciente cadastrado.
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => navigate('/patients')}
        >
          <UserPlus />
          Cadastrar paciente
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-2">
      {patients.map((patient) => {
        const active = patient.id === selectedId
        return (
          <button
            key={patient.id}
            type="button"
            onClick={() => onSelect(patient)}
            aria-pressed={active}
            className={cn(
              'inline-flex min-h-9 items-center gap-1.5 rounded-3xl border px-3 py-1.5',
              'text-body-md font-medium transition-all outline-none',
              'focus-visible:ring-3 focus-visible:ring-ring/30',
              active
                ? 'border-transparent bg-primary text-primary-foreground'
                : 'border-border bg-card text-foreground hover:bg-muted',
            )}
          >
            {active && <Check size={14} />}
            {patient.nome}
          </button>
        )
      })}
    </div>
  )
}

export default PatientSelector
