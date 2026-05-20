import {
  Bug,
  Droplets,
  Flame,
  HeartPulse,
  Leaf,
  Pill,
  Thermometer,
  Wind,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Medication } from '../types'

function normalizeCategory(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
}

export function CategoryIcon({
  category,
  size = 20,
}: {
  category: string
  size?: number
}) {
  const props = { size, strokeWidth: 2 }
  switch (normalizeCategory(category)) {
    case 'antacidos':
      return <Flame {...props} />
    case 'antibioticos':
      return <Bug {...props} />
    case 'analgesicos':
      return <Thermometer {...props} />
    case 'antihistaminicos':
      return <Leaf {...props} />
    case 'cardiacos':
      return <HeartPulse {...props} />
    case 'diureticos':
      return <Droplets {...props} />
    case 'broncodilatadores':
      return <Wind {...props} />
    default:
      return <Pill {...props} />
  }
}

interface MedicationCardProps {
  medication: Medication
  onSelect: (id: number) => void
  style?: React.CSSProperties
}

function MedicationCard({ medication, onSelect, style }: MedicationCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(medication.id)}
      style={style}
      className={cn(
        'group flex flex-col gap-3 rounded-3xl border border-border bg-card p-4 text-left',
        'transition-all duration-200 outline-none',
        'hover:-translate-y-0.5 hover:border-arca-blue-300 hover:shadow-md',
        'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30',
        'active:translate-y-0',
      )}
    >
      <span
        className={cn(
          'flex size-11 items-center justify-center rounded-2xl',
          'bg-arca-blue-100 text-arca-blue-600',
          'transition-colors group-hover:bg-arca-blue-600 group-hover:text-white',
        )}
      >
        <CategoryIcon category={medication.category} />
      </span>

      <div className="flex flex-col gap-0.5">
        <h3 className="font-heading text-body-lg leading-tight font-semibold text-foreground">
          {medication.name}
        </h3>
        <p className="text-body-md font-medium text-arca-blue-600">
          {medication.category}
        </p>
        <p className="mt-0.5 line-clamp-2 text-caption text-muted-foreground">
          {medication.description}
        </p>
      </div>
    </button>
  )
}

export default MedicationCard
