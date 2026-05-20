import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav-items";

/**
 * Passo horizontal entre os centros das 3 abas (= deslocamento do domo), em px.
 * Barra de 290px, padding lateral 32px (px-8) → interior 226px / 3 ≈ 75px por aba.
 * A largura (290) e o padding são escolhidos para que o domo de 94px
 * acompanhe a aba das pontas sem ultrapassar os cantos arredondados.
 */
const TAB_STEP = 75;

export function ClipboardNav() {
  const { pathname } = useLocation();
  const activeIndex = NAV_ITEMS.findIndex((item) => item.match(pathname));
  const hasActive = activeIndex >= 0;
  const domeOffset = Math.max(activeIndex, 0) - 1; // -1 | 0 | 1

  return (
    <nav
      aria-label="Navegação principal"
      className={cn(
        "fixed left-4 z-40 h-25 w-72.5 tablet:hidden",
        "bottom-[calc(1rem+env(safe-area-inset-bottom))]",
      )}
    >
      {/* domo central — desliza até a aba ativa */}
      <svg
        aria-hidden
        className={cn(
          "absolute left-1/2 top-9 z-10 transition-[transform,opacity] duration-200 ease-out",
          "motion-reduce:transition-none",
          hasActive ? "opacity-100" : "opacity-0",
        )}
        style={{
          transform: `translateX(calc(-50% + ${domeOffset * TAB_STEP}px))`,
        }}
        width="94"
        height="53"
        viewBox="0 0 94 53"
        fill="none"
      >
        <path
          d="M93.0511 17.4068C71.2294 20.308 78.6405 52.6349 45.7021 52.6349C12.7636 52.6349 22.111 20.2759 0 17.4068C0 3.44433 30.6942 0 45.7021 0C60.71 0 93.0511 3.44433 93.0511 17.4068Z"
          fill="var(--arca-blue-800)"
        />
      </svg>

      {/* barra */}
      <div className="absolute bottom-0 left-0 flex h-12 w-72.5 items-center rounded-[296px] bg-arca-blue-600 px-8">
        {NAV_ITEMS.map((item, i) => {
          const active = i === activeIndex;
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex h-11 flex-1 items-center justify-center rounded-2xl outline-none",
                "focus-visible:ring-2 focus-visible:ring-white/70",
              )}
            >
              <Icon
                aria-hidden
                strokeWidth={2.25}
                className={cn(
                  "size-5.5 text-white transition-[transform,opacity] duration-200 ease-out",
                  "motion-reduce:transition-none",
                  // ativo: sobe e se apoia no domo, acima dele
                  active ? "relative z-20 -translate-y-3.75" : "opacity-55",
                )}
              />
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
