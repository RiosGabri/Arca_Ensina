import { useState } from 'react'
import type { CalculatorFormData } from '../types'
import { useCalculateDose } from '../api'

const EMPTY_FORM: CalculatorFormData = {
  weight: null,
  height: null,
  age_days: null,
  medication_id: null,
}

export function useCalculatorForm() {
  const [formData, setFormData] = useState<CalculatorFormData>(EMPTY_FORM)
  const mutation = useCalculateDose()

  function handleCalculate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    mutation.mutate(formData)
  }

  function calculate(data: CalculatorFormData) {
    mutation.mutate(data)
  }

  function resetResult() {
    mutation.reset()
  }

  return {
    formData,
    setFormData,
    result: mutation.data ?? null,
    loading: mutation.isPending,
    error: mutation.isError ? 'Erro ao calcular a medicação.' : null,
    handleCalculate,
    calculate,
    resetResult,
  }
}
