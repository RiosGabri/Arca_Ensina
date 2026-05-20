import { Check, Dot } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Patient } from '../types';

function formatAge(dataNascimento: string): string {
  const birth = new Date(dataNascimento);
  const now = new Date();
  const years = Math.floor(
    (now.getTime() - birth.getTime()) / (365.25 * 24 * 60 * 60 * 1000),
  );
  if (years < 1) {
    const months = Math.floor(
      (now.getTime() - birth.getTime()) / (30.44 * 24 * 60 * 60 * 1000),
    );
    return `${months} ${months === 1 ? 'mês' : 'meses'}`;
  }
  return `${years} ${years === 1 ? 'ano' : 'anos'}`;
}

interface PatientPillProps {
  patient: Patient;
  active?: boolean;
  onClick?: () => void;
  size?: 'default' | 'lg';
}

export default function PatientPill({ patient, active, onClick, size = 'default' }: PatientPillProps) {
  const Comp = onClick ? 'button' : 'div';

  return (
    <Comp
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      aria-pressed={onClick ? active : undefined}
      className={cn(
        'inline-flex flex-col items-start rounded-2xl transition-all',
        size === 'default' && 'min-w-36 max-w-48 px-3.5 py-3',
        size === 'lg' && 'min-w-44 max-w-56 px-5 py-4',
        onClick && 'cursor-pointer outline-none focus-visible:ring-3 focus-visible:ring-ring/30',
        active
          ? 'border-transparent bg-primary text-primary-foreground'
          : 'border border-border bg-background hover:bg-muted',
      )}
    >
      <span className={cn(
        'flex w-full items-center gap-1.5 font-bold truncate',
        size === 'default' ? 'text-body-md' : 'text-body-lg',
      )}>
        {active && <Check size={size === 'lg' ? 16 : 14} className="shrink-0" />}
        <span className="truncate">{patient.nome}</span>
      </span>
      <span className={cn(
        'flex items-center',
        size === 'default' ? 'text-caption' : 'text-body-md',
        active ? 'text-primary-foreground/70' : 'text-muted-foreground',
      )}>
        {formatAge(patient.dataNascimento)}
        <Dot className="size-3" />
        {patient.genero}
      </span>
    </Comp>
  );
}
