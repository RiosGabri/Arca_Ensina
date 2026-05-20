import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export type SyncStatus = "online" | "syncing" | "offline" | "error";

const CONFIG: Record<SyncStatus, { label: string; dot: string; text: string }> = {
  online: { label: "Conectado", dot: "bg-success", text: "text-neutral-700" },
  syncing: { label: "Sincronizando…", dot: "bg-info animate-pulse", text: "text-neutral-700" },
  offline: { label: "Offline — salvo no aparelho", dot: "bg-warning", text: "text-neutral-700" },
  error: { label: "Erro de sincronização", dot: "bg-danger", text: "text-danger" },
};

interface SyncIndicatorProps {
  /** Estado forçado. Se omitido, deriva de `navigator.onLine`. */
  status?: SyncStatus;
  /** Nº de operações pendentes (FR26) — exibido quando offline. */
  pendingCount?: number;
}

/**
 * Indicador de conectividade do shell (CORE-013 / FR26). Quatro estados com
 * cor + rótulo visível e `aria-live` para leitores de tela. A sincronização
 * real chega em EXP-001a (S2) — por ora reage só a online/offline do browser.
 */
export function SyncIndicator({ status, pendingCount = 0 }: SyncIndicatorProps) {
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  const resolved: SyncStatus = status ?? (online ? "online" : "offline");
  const cfg = CONFIG[resolved];
  const label =
    resolved === "offline" && pendingCount > 0
      ? `Offline — ${pendingCount} ${pendingCount === 1 ? "decisão salva" : "decisões salvas"} no aparelho`
      : cfg.label;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "fixed right-3 top-3 z-40 flex items-center gap-2 rounded-full",
        "border border-neutral-200 bg-white/90 px-3 py-1.5 shadow-sm backdrop-blur",
        "text-caption font-medium",
        cfg.text,
      )}
    >
      <span aria-hidden className={cn("size-2 rounded-full", cfg.dot)} />
      {label}
    </div>
  );
}
