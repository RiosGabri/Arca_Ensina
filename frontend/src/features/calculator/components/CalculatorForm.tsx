import { useState } from 'react'
import UnitInput from '@/components/ui/unitInput'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { CalculatorFormData, CalculatorFormDisplay } from '../types'
import { EMPTY_DISPLAY } from '../types'
import { convertWeight, convertHeight, convertAge } from '../conversions'

interface CalculatorFormProps {
  formData: CalculatorFormData
  onChange: (data: CalculatorFormData) => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  loading: boolean
  initialDisplay?: CalculatorFormDisplay
}

function CalculatorForm(props: CalculatorFormProps) {
  const initial = props.initialDisplay ?? EMPTY_DISPLAY

  const [weightValue, setWeightValue] = useState(initial.weight)
  const [heightValue, setHeightValue] = useState(initial.height)
  const [weightUnit, setWeightUnit] = useState<'kg' | 'g'>(initial.weightUnit)
  const [heightUnit, setHeightUnit] = useState<'cm' | 'm'>(initial.heightUnit)
  const [years, setYears] = useState(initial.years)
  const [months, setMonths] = useState(initial.months)

  function ageChange(newYears: string, newMonths: string) {
    const y = parseInt(newYears) || 0
    const m = parseInt(newMonths) || 0
    const days = convertAge(y, m)
    props.onChange({ ...props.formData, age_days: days })
  }

  return (
    <form onSubmit={props.onSubmit}>
      <div className="flex flex-col gap-4">
        <UnitInput
          label="Peso"
          value={weightValue ?? ''}
          placeholder="Digite o peso"
          onChange={(value) => {
            setWeightValue(value)
            const parsed = parseFloat(value)
            props.onChange({
              ...props.formData,
              weight: isNaN(parsed) ? null : parsed,
            })
          }}
          units={['kg', 'g']}
          unit={weightUnit}
          onUnitChange={(newUnit) => {
            const unit = newUnit as 'kg' | 'g'
            if (props.formData.weight !== null) {
              props.onChange({
                ...props.formData,
                weight: convertWeight(props.formData.weight, unit),
              })
            }
            setWeightUnit(unit)
          }}
        />
        <UnitInput
          label="Altura (opcional)"
          value={heightValue ?? ''}
          placeholder="Digite a altura"
          onChange={(value) => {
            setHeightValue(value)
            const parsed = parseFloat(value)
            props.onChange({
              ...props.formData,
              height: isNaN(parsed) ? null : parsed,
            })
          }}
          unit={heightUnit}
          units={['cm', 'm']}
          onUnitChange={(newUnit) => {
            const unit = newUnit as 'cm' | 'm'
            if (props.formData.height !== null) {
              props.onChange({
                ...props.formData,
                height: convertHeight(props.formData.height, unit),
              })
            }
            setHeightUnit(unit)
          }}
        />

        <div className="flex flex-col gap-2">
          <span className="text-body-md font-medium text-foreground">
            Idade
          </span>
          <div className="grid grid-cols-2 gap-3">
            <Input
              type="number"
              min={0}
              placeholder="Anos"
              value={years}
              onChange={(e) => {
                setYears(e.target.value)
                ageChange(e.target.value, months)
              }}
            />
            <Input
              type="number"
              min={0}
              max={11}
              placeholder="Meses"
              value={months}
              onChange={(e) => {
                setMonths(e.target.value)
                ageChange(years, e.target.value)
              }}
            />
          </div>
        </div>

        <Button
          type="submit"
          variant="default"
          size="lg"
          disabled={props.loading}
          className="mt-2 w-full"
        >
          {props.loading ? 'Calculando...' : 'Calcular dose'}
        </Button>
      </div>
    </form>
  )
}

export default CalculatorForm
