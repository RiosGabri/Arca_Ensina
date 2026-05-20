import { AlertTriangle, OctagonAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CalculationResult, WarningLevel } from "../types";

function frequencyLabel(freq: number): string {
  const labels: Record<number, string> = {
    1: "1x ao dia (24/24h)",
    2: "2x ao dia (12/12h)",
    3: "3x ao dia (8/8h)",
    4: "4x ao dia (6/6h)",
    6: "6x ao dia (4/4h)",
  };
  return labels[freq] ?? `${freq}x ao dia`;
}

const WARNING_COPY: Record<WarningLevel, string> = {
  BAIXO: "Dose abaixo do mínimo recomendado.",
  ALTO: "Dose acima do máximo recomendado.",
  CRITICO: "Dose acima do teto absoluto | revise a prescrição.",
};

function WarningAlert({ level }: { level: WarningLevel }) {
  const critical = level === "CRITICO";
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-2xl border p-3",
        critical
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : "border-warning/40 bg-warning/10 text-warning",
      )}
    >
      {critical ? (
        <OctagonAlert size={18} className="mt-0.5 shrink-0" />
      ) : (
        <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      )}
      <p className="text-body-md font-medium">
        {WARNING_COPY[level]} <span className="font-semibold">({level})</span>
      </p>
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-4">
      <span className="text-caption font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </span>
      <span className="text-numeric-md font-semibold text-foreground">
        {value}
      </span>
    </div>
  );
}

interface CalculatorResultProps {
  result: CalculationResult;
}

function CalculatorResult({ result }: CalculatorResultProps) {
  const frequencyText = frequencyLabel(result.frequency_per_day);

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-caption font-semibold tracking-wider text-muted-foreground uppercase">
        Resultado do cálculo
      </h2>

      {result.warnings.length > 0 && (
        <div className="flex flex-col gap-2">
          {result.warnings.map((level) => (
            <WarningAlert key={level} level={level} />
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatTile label="Dose diária" value={`${result.dosage_mg} mg`} />
        <StatTile label="Por dose" value={`${result.dosage_per_dose} mg`} />
        <StatTile
          label="Frequência"
          value={`${result.frequency_per_day}x ao dia`}
        />
      </div>

      <div className="flex flex-col gap-2 rounded-3xl bg-arca-blue-600 p-5 text-white">
        <span className="text-caption font-medium tracking-wide text-white/70 uppercase">
          {result.volume_ml !== null ? "Volume por dose" : "Administração"}
        </span>
        {result.volume_ml !== null && (
          <span className="text-numeric-hero leading-none font-bold">
            {result.volume_ml}{" "}
            <span className="text-numeric-md font-semibold">mL</span>
          </span>
        )}
        <p className="text-body-md text-white/90">
          Administrar {result.dosage_per_dose} mg por dose
          {result.volume_ml !== null && ` (${result.volume_ml} mL)`},{" "}
          {frequencyText}.
        </p>
      </div>
    </section>
  );
}

export default CalculatorResult;
