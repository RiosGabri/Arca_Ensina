import { useNavigate } from "react-router-dom";
import { ArrowLeft, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { CategoryIcon } from "./MedicationCard";
import type { RecentMedication } from "../hooks/useRecentMedications";

interface CalculatorSidebarProps {
  recents: RecentMedication[];
  currentId: number | null;
}

function CalculatorSidebar({ recents, currentId }: CalculatorSidebarProps) {
  const navigate = useNavigate();
  const otherRecents = recents.filter((m) => m.id !== currentId);

  return (
    <aside className="hidden lg:flex lg:flex-col lg:gap-6">
      <Button
        type="button"
        variant="outline"
        onClick={() => navigate("/medications")}
        className="w-full justify-start"
      >
        <ArrowLeft />
        Voltar aos medicamentos
      </Button>

      <div className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Clock size={16} />
          <h2 className="text-caption font-semibold tracking-wider uppercase">
            Recentes
          </h2>
        </div>

        {otherRecents.length === 0 ? (
          <p className="text-body-md text-muted-foreground">
            Os medicamentos que você calcular aparecem aqui.
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {otherRecents.map((medication) => (
              <li key={medication.id}>
                <button
                  type="button"
                  onClick={() =>
                    navigate(`/calculator/calculate/${medication.id}`)
                  }
                  className={cn(
                    "flex w-full items-center gap-3 rounded-2xl p-2 text-left transition-colors",
                    "hover:bg-muted focus-visible:bg-muted focus-visible:outline-none",
                  )}
                >
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-arca-blue-100 text-arca-blue-600">
                    <CategoryIcon category={medication.category} size={16} />
                  </span>
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate text-body-md font-medium text-foreground">
                      {medication.name}
                    </span>
                    <span className="truncate text-caption text-muted-foreground">
                      {medication.category}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

export default CalculatorSidebar;
