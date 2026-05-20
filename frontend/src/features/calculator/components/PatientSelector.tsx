import { UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { usePatients, PatientPill, type Patient } from '@/features/patient'

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
          <Skeleton key={i} className="h-14 w-36 rounded-2xl" />
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
      {patients.map((patient) => (
        <PatientPill
          key={patient.id}
          patient={patient}
          active={patient.id === selectedId}
          onClick={() => onSelect(patient)}
        />
      ))}
    </div>
  )
}

export default PatientSelector
