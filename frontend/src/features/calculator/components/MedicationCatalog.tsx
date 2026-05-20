import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PackageOpen, Search, SlidersHorizontal, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { useMedications } from "../api";
import MedicationCard from "./MedicationCard";

const ALL = "Todos";

function CategoryChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={active ? "default" : "outline"}
      onClick={onClick}
      className="shrink-0"
    >
      {label}
    </Button>
  );
}

function MedicationCatalog() {
  const navigate = useNavigate();
  const { data: medications = [], isLoading, isError } = useMedications();

  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string>(ALL);

  const categories = useMemo(() => {
    const unique = [...new Set(medications.map((m) => m.category))].sort(
      (a, b) => a.localeCompare(b, "pt-BR"),
    );
    return [ALL, ...unique];
  }, [medications]);

  const results = useMemo(() => {
    const term = query.trim().toLowerCase();
    return medications.filter((m) => {
      const matchesCategory = category === ALL || m.category === category;
      const matchesTerm = m.name.toLowerCase().includes(term);
      return matchesCategory && matchesTerm;
    });
  }, [medications, query, category]);

  function handleSelect(id: number) {
    navigate(`/calculator/calculate/${id}`);
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      {/* Busca + Filtros */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search
            size={18}
            className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar medicamento..."
            aria-label="Buscar medicamento"
            className="bg-card pl-11 ring-1 ring-border"
          />
        </div>

        <Sheet>
          <SheetTrigger asChild>
            <Button type="button" variant="outline">
              <SlidersHorizontal />
              <span className="hidden sm:inline">Filtros</span>
            </Button>
          </SheetTrigger>
          <SheetContent className="w-80 max-w-[85vw]">
            <SheetHeader>
              <SheetTitle>Filtros</SheetTitle>
            </SheetHeader>
            <div className="flex flex-col gap-1 px-4">
              <p className="px-1 pb-1 text-caption font-medium tracking-wide text-muted-foreground uppercase">
                Categoria
              </p>
              {categories.map((cat) => (
                <SheetClose asChild key={cat}>
                  <button
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={cn(
                      "flex h-11 items-center rounded-2xl px-3 text-left text-body-md transition-colors",
                      "hover:bg-muted focus-visible:bg-muted focus-visible:outline-none",
                      category === cat
                        ? "bg-arca-blue-50 font-semibold text-arca-blue-700"
                        : "text-foreground",
                    )}
                  >
                    {cat}
                  </button>
                </SheetClose>
              ))}
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Chips de categoria */}
      <div className="-mx-1 mt-4 flex gap-2 overflow-x-auto px-1 pb-1 scrollbar:none [&::-webkit-scrollbar]:hidden">
        {categories.map((cat) => (
          <CategoryChip
            key={cat}
            label={cat}
            active={category === cat}
            onClick={() => setCategory(cat)}
          />
        ))}
      </div>

      {/* Cabeçalho dos resultados */}
      <div className="mt-6 flex items-baseline justify-between">
        <p className="text-caption font-semibold tracking-wider text-muted-foreground uppercase">
          Resultados
        </p>
        {!isLoading && !isError && (
          <span className="text-caption text-muted-foreground">
            {results.length}{" "}
            {results.length === 1 ? "medicamento" : "medicamentos"}
          </span>
        )}
      </div>

      {/* Grade */}
      {isError ? (
        <div className="mt-10 flex flex-col items-center gap-3 text-center">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
            <X size={22} />
          </span>
          <p className="text-body-lg font-medium text-foreground">
            Não foi possível carregar os medicamentos
          </p>
          <p className="text-body-md text-muted-foreground">
            Verifique a conexão e tente novamente.
          </p>
        </div>
      ) : isLoading ? (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-4"
            >
              <Skeleton className="size-11 rounded-2xl" />
              <div className="flex flex-col gap-1.5">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-3 w-full" />
              </div>
            </div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <div className="mt-10 flex flex-col items-center gap-3 text-center">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <PackageOpen size={22} />
          </span>
          <p className="text-body-lg font-medium text-foreground">
            {query.trim()
              ? `Nenhum resultado para "${query.trim()}"`
              : "Nenhum medicamento nesta categoria"}
          </p>
          <p className="text-body-md text-muted-foreground">
            Ajuste a busca ou selecione outra categoria.
          </p>
        </div>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {results.map((medication, i) => (
            <MedicationCard
              key={medication.id}
              medication={medication}
              onSelect={handleSelect}
              style={{
                animation: "fade-in-up 0.3s ease-out backwards",
                animationDelay: `${Math.min(i, 11) * 30}ms`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default MedicationCatalog;
