import { useEffect, useRef, useState } from "react";
import { Loader2, TriangleAlert } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Patient } from "@/features/patient";
import type {
  Medication,
  CalculatorFormData,
  CalculatorFormDisplay,
} from "../types";
import { EMPTY_DISPLAY } from "../types";
import { convertBirthDate } from "../conversions";
import { useCalculatorForm } from "../hooks/useCalculatorForm";
import CalculatorMedicationInfo from "./CalculatorMedicationInfo";
import CalculatorForm from "./CalculatorForm";
import CalculatorResult from "./CalculatorResult";
import PatientSelector from "./PatientSelector";

type Mode = "patient" | "manual";

function ageToYearsMonths(ageDays: number): { years: number; months: number } {
  return {
    years: Math.floor(ageDays / 365),
    months: Math.floor((ageDays % 365) / 30),
  };
}

interface DerivedPatient {
  data: CalculatorFormData;
  weightLabel: string | null;
  heightLabel: string | null;
  ageLabel: string | null;
}

function derivePatient(patient: Patient, medicationId: number): DerivedPatient {
  const weight = patient.peso ? parseFloat(patient.peso) : NaN;
  const height = patient.altura ? parseFloat(patient.altura) : NaN;

  let ageDays: number | null = null;
  try {
    ageDays = convertBirthDate(patient.dataNascimento);
  } catch {
    ageDays = null;
  }
  const ageParts = ageDays !== null ? ageToYearsMonths(ageDays) : null;

  return {
    data: {
      weight: isNaN(weight) ? null : weight,
      height: isNaN(height) ? null : height,
      age_days: ageDays,
      medication_id: medicationId,
    },
    weightLabel: isNaN(weight) ? null : `${weight} kg`,
    heightLabel: isNaN(height) ? null : `${height} cm`,
    ageLabel: ageParts ? `${ageParts.years}a ${ageParts.months}m` : null,
  };
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-2xl bg-muted px-3 py-2">
      <span className="text-caption font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </span>
      <span className="text-body-lg font-semibold text-foreground">
        {value}
      </span>
    </div>
  );
}

interface CalculatorWorkspaceProps {
  medication: Medication;
}

function CalculatorWorkspace({ medication }: CalculatorWorkspaceProps) {
  const {
    formData,
    setFormData,
    result,
    loading,
    error,
    handleCalculate,
    calculate,
    resetResult,
  } = useCalculatorForm();

  const [mode, setMode] = useState<Mode>("patient");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [display, setDisplay] = useState<CalculatorFormDisplay>(EMPTY_DISPLAY);
  const [formKey, setFormKey] = useState("manual");

  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFormData((prev) => ({ ...prev, medication_id: medication.id }));
  }, [medication.id, setFormData]);

  useEffect(() => {
    if (result) {
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  function switchMode(next: Mode) {
    setMode(next);
    setSelectedPatient(null);
    setDisplay(EMPTY_DISPLAY);
    setFormData({
      weight: null,
      height: null,
      age_days: null,
      medication_id: medication.id,
    });
    setFormKey(`${next}-empty`);
    resetResult();
  }

  function handlePatientSelect(patient: Patient) {
    setSelectedPatient(patient);
    resetResult();
    const { data } = derivePatient(patient, medication.id);
    if (data.weight !== null) {
      calculate(data);
    }
  }

  const derived = selectedPatient
    ? derivePatient(selectedPatient, medication.id)
    : null;
  const missingWeight = derived !== null && derived.data.weight === null;

  return (
    <div className="flex flex-col gap-6">
      <CalculatorMedicationInfo medication={medication} />

      <Tabs value={mode} onValueChange={(value) => switchMode(value as Mode)}>
        <TabsList className="w-full">
          <TabsTrigger value="patient">A partir de paciente</TabsTrigger>
          <TabsTrigger value="manual">Manual</TabsTrigger>
        </TabsList>
      </Tabs>

      {mode === "patient" && (
        <div className="flex flex-col gap-3">
          <span className="text-body-md font-medium text-foreground">
            Selecione o paciente
          </span>
          <PatientSelector
            selectedId={selectedPatient?.id ?? null}
            onSelect={handlePatientSelect}
          />

          {derived && (
            <div className="grid grid-cols-3 gap-2">
              <SummaryTile label="Peso" value={derived.weightLabel ?? "|"} />
              <SummaryTile label="Altura" value={derived.heightLabel ?? "|"} />
              <SummaryTile label="Idade" value={derived.ageLabel ?? "|"} />
            </div>
          )}

          {missingWeight && (
            <p className="flex items-start gap-2 rounded-2xl border border-warning/40 bg-warning/10 p-3 text-body-md font-medium text-warning">
              <TriangleAlert size={18} className="mt-0.5 shrink-0" />
              Este paciente não tem peso registrado. Cadastre o peso ou use a
              calculadora manual.
            </p>
          )}

          {loading && (
            <p className="flex items-center gap-2 text-body-md text-muted-foreground">
              <Loader2 size={16} className="animate-spin" />
              Calculando dose...
            </p>
          )}
        </div>
      )}

      {result && (
        <div
          ref={resultRef}
          style={{ animation: "fade-in-up 0.35s ease-out" }}
          className="scroll-mt-6"
        >
          <CalculatorResult result={result} />
        </div>
      )}
      {error && (
        <p className="rounded-2xl border border-destructive/30 bg-destructive/10 p-3 text-body-md font-medium text-destructive">
          {error}
        </p>
      )}

      {mode === "manual" && (
        <div className="rounded-3xl border border-border bg-card p-5">
          <CalculatorForm
            key={formKey}
            formData={formData}
            onChange={setFormData}
            onSubmit={handleCalculate}
            loading={loading}
            initialDisplay={display}
          />
        </div>
      )}
    </div>
  );
}

export default CalculatorWorkspace;
