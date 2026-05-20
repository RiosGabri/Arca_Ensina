import { useMutation, useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import type { Medication, CalculatorFormData, CalculationResult } from './types'

export const useMedications = () =>
  useQuery({
    queryKey: ['medications', 'list'],
    queryFn: async () => {
      const res = await api.get<Medication[]>('medications')
      return res.data
    },
    staleTime: 5 * 60_000,
  })

export const useMedication = (id: number | null) =>
  useQuery({
    queryKey: ['medications', 'detail', id],
    queryFn: async () => {
      const res = await api.get<Medication>(`medications/${id}`)
      return res.data
    },
    enabled: id !== null && !Number.isNaN(id),
    staleTime: 5 * 60_000,
  })

export const useCalculateDose = () =>
  useMutation({
    mutationFn: async (data: CalculatorFormData) => {
      const res = await api.post<CalculationResult>('calculator/calculate/', data)
      return res.data
    },
    retry: 0, // safety-critical: no automatic retry
  })
