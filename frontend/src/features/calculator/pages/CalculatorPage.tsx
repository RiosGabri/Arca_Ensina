import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, PillBottle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useMedication } from '../api'
import { useRecentMedications } from '../hooks/useRecentMedications'
import CalculatorSidebar from '../components/CalculatorSidebar'
import CalculatorWorkspace from '../components/CalculatorWorkspace'

function WorkspaceSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-full" />
      </div>
      <Skeleton className="h-11 w-full rounded-full" />
      <Skeleton className="h-64 w-full rounded-3xl" />
    </div>
  )
}

function MedicationError() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <span className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <PillBottle size={22} />
      </span>
      <p className="text-body-lg font-medium text-foreground">
        Medicamento não encontrado
      </p>
      <p className="text-body-md text-muted-foreground">
        O medicamento pode ter sido removido ou o endereço está incorreto.
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => navigate('/medications')}
      >
        Ver medicamentos
      </Button>
    </div>
  )
}

function CalculatorPage() {
  const navigate = useNavigate()
  const { medicationId } = useParams<{ medicationId: string }>()
  const id = medicationId ? Number(medicationId) : null
  const validId = id !== null && !Number.isNaN(id)

  const {
    data: medication,
    isLoading,
    isError,
  } = useMedication(validId ? id : null)
  const { recents, addRecent } = useRecentMedications()

  useEffect(() => {
    if (medication) addRecent(medication)
  }, [medication, addRecent])

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => navigate('/medications')}
          className="mb-4 -ml-2 lg:hidden"
        >
          <ArrowLeft />
          Voltar
        </Button>

        <div className="lg:grid lg:grid-cols-[260px_1fr] lg:gap-8">
          <CalculatorSidebar recents={recents} currentId={validId ? id : null} />
          <main className="min-w-0">
            {!validId || isError ? (
              <MedicationError />
            ) : isLoading ? (
              <WorkspaceSkeleton />
            ) : medication ? (
              <CalculatorWorkspace medication={medication} />
            ) : null}
          </main>
        </div>
      </div>
    </div>
  )
}

export default CalculatorPage
