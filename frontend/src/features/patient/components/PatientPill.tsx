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
}

export default function PatientPill({ patient, active, onClick }: PatientPillProps) {
  const Comp = onClick ? 'button' : 'div';

  return (
    <Comp
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      aria-pressed={onClick ? active : undefined}
      className={cn(
        'inline-flex min-w-36 max-w-48 flex-col items-start rounded-2xl px-3.5 py-3 transition-all',
        onClick && 'cursor-pointer outline-none focus-visible:ring-3 focus-visible:ring-ring/30',
        active
          ? 'border-transparent bg-primary text-primary-foreground'
          : 'border border-border bg-background hover:bg-muted',
      )}
    >
      <span className="flex w-full items-center gap-1.5 text-body-md font-bold truncate">
        {active && <Check size={14} className="shrink-0" />}
        <span className="truncate">{patient.nome}</span>
      </span>
      <span className={cn(
        'flex items-center text-caption',
        active ? 'text-primary-foreground/70' : 'text-muted-foreground',
      )}>
        {formatAge(patient.dataNascimento)}
        <Dot className="size-3" />
        {patient.genero}
      </span>
    </Comp>
  );
}
