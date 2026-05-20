import type { Medication } from '../types'

function CalculatorMedicationInfo({ medication }: { medication: Medication }) {
  return (
    <div className="flex flex-col gap-1">
      <h1 className="font-heading text-display-sm font-bold text-foreground">
        {medication.name}
      </h1>
      <p className="text-body-lg font-semibold text-arca-blue-600">
        {medication.category}
      </p>
      <p className="mt-1 text-body-md text-muted-foreground">
        {medication.description}
      </p>
    </div>
  )
}

export default CalculatorMedicationInfo
