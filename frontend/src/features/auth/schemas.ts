import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(1, 'Senha obrigatória'),
})

export type LoginInput = z.infer<typeof loginSchema>

export const registerSchema = z.object({
  first_name: z.string().min(1, 'Nome obrigatório'),
  last_name: z.string().min(1, 'Sobrenome obrigatório'),
  gender: z.enum(['masculino', 'feminino', 'outro', 'nao_informado'], {
    message: 'Gênero obrigatório',
  }),
  birth_date: z.string().min(1, 'Data de nascimento obrigatória'),
  password: z.string().min(8, 'Senha deve ter no mínimo 8 caracteres'),
})

export type RegisterInput = z.infer<typeof registerSchema>
