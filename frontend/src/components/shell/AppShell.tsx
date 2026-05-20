import type { ReactNode } from "react";
import { ClipboardNav } from "./ClipboardNav";
import { DesktopNav } from "./DesktopNav";
import { EmergencyButton } from "./EmergencyButton";

/**
 * Estrutura global de todas as rotas autenticadas (CORE-013 / UX-DR6):
 * NavBar (desktop/iPad) ou TabBar "prancheta" (mobile) e FAB de emergência.
 * Landmarks `<nav>` e `<main>`.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen bg-background">
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-arca-blue-700 focus:px-4 focus:py-2 focus:text-white"
      >
        Pular para o conteúdo
      </a>

      <DesktopNav />
      <ClipboardNav />

      {/* padding reserva espaço para a nav fixa: rodapé no mobile, topo no desktop */}
      <main id="conteudo" className="w-full pb-32 pt-4 tablet:pb-16 tablet:pt-28">
        {children}
      </main>

      <EmergencyButton />
    </div>
  );
}
