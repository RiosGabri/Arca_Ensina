// dados recebidos da lista de medicamentos
export interface Medication {
  id: number
  name: string
  category: string
  description: string
}

// dados enviados no formulário de cálculo
export interface CalculatorFormData {
  weight: number | null
  height: number | null
  age_days: number | null
  medication_id: number | null
}

// valores de exibição do formulário (strings dos inputs + unidades)
export interface CalculatorFormDisplay {
  weight: string
  weightUnit: 'kg' | 'g'
  height: string
  heightUnit: 'cm' | 'm'
  years: string
  months: string
}

export const EMPTY_DISPLAY: CalculatorFormDisplay = {
  weight: '',
  weightUnit: 'kg',
  height: '',
  heightUnit: 'cm',
  years: '',
  months: '',
}

// níveis de warning
export type WarningLevel = 'BAIXO' | 'ALTO' | 'CRITICO'

// dados que o backend retorna após o cálculo
export interface CalculationResult {
  dosage_mg: number
  dosage_per_dose: number
  frequency_per_day: number
  volume_ml: number | null // null se o medicamento não tem concentração
  warnings: WarningLevel[]
}
