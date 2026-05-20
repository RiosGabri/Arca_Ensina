import { useEffect } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface EmergencyButtonProps {
  /**
   * Ação ao acionar. Quando ausente exibe um stub — o `EmergencyProtocolSheet`
   * (bottom sheet) chega em CORE-010 (S3) e deve ser ligado aqui.
   */
  onActivate?: () => void;
}

/**
 * FAB de Modo Emergência (CORE-013 / UX-DR3). 64×64, fixo no canto inferior
 * direito em todas as rotas autenticadas, atalho `Alt+E`.
 */
export function EmergencyButton({ onActivate }: EmergencyButtonProps) {
  function activate() {
    if (onActivate) {
      onActivate();
      return;
    }
    toast("Modo emergência", {
      description: "Acesso a protocolos críticos disponível a partir do Sprint 3 (CORE-010).",
    });
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.altKey && (e.key === "e" || e.key === "E")) {
        e.preventDefault();
        activate();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  return (
    <button
      type="button"
      onClick={activate}
      aria-label="Modo emergência (atalho: Alt + E)"
      className={cn(
        "fixed right-5 z-50 grid size-14 place-items-center rounded-[2rem]",
        "bg-arca-red-600 text-white",
        "shadow-[0_10px_30px_-4px_rgba(212,9,36,0.5)]",
        "transition-transform duration-150 hover:scale-105 active:scale-95 motion-reduce:transition-none",
        "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-arca-red-300",
        // mobile: ancorado logo acima da TabBar do rodapé; desktop: canto inferior
        "bottom-[calc(1.25rem+env(safe-area-inset-bottom))] tablet:bottom-6",
      )}
    >
      <Plus className="size-8" strokeWidth={3} aria-hidden />
    </button>
  );
}
