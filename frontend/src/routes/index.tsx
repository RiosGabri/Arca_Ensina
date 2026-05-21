import { type ReactNode } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router";
import { useAuth } from "@/features/auth";
import { AppShell } from "@/components/shell/AppShell";

function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <p className="text-center mt-20">Carregando...</p>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

/** Layout das rotas autenticadas: exige sessão e envolve tudo no AppShell. */
function ShellLayout() {
  return (
    <RequireAuth>
      <AppShell>
        <Outlet />
      </AppShell>
    </RequireAuth>
  );
}

const router = createBrowserRouter([
  {
    element: <ShellLayout />,
    children: [
      {
        path: "/dashboard",
        lazy: () =>
          import("@/pages/Dashboard").then((m) => ({ Component: m.default })),
      },
      {
        path: "/_/design-system",
        lazy: () =>
          import("@/pages/DesignSystem").then((m) => ({ Component: m.default })),
      },
      {
        path: "/patients",
        lazy: () =>
          import("@/features/patient/pages/PatientCreatePage").then((m) => ({
            Component: m.default,
          })),
      },
      {
        path: "/patients/list",
        lazy: () =>
          import("@/pages/PatientListPage").then((m) => ({
            Component: m.default,
          })),
      },
      {
        path: "/medications",
        lazy: () =>
          import("@/features/calculator/pages/MedicationSelectPage").then(
            (m) => ({ Component: m.default }),
          ),
      },
      {
        path: "/repositorio",
        lazy: () =>
          import("@/pages/Repositorio").then((m) => ({ Component: m.default })),
      },
      {
        path: "/calculator/calculate/:medicationId",
        lazy: () =>
          import("@/features/calculator/pages/CalculatorPage").then((m) => ({
            Component: m.default,
          })),
      },
    ],
  },
  {
    path: "/login",
    lazy: () =>
      import("@/features/auth/pages/LoginPage").then((m) => ({
        Component: m.default,
      })),
  },
  {
    path: "/invite/:token",
    lazy: () =>
      import("@/features/auth/pages/InvitePage").then((m) => ({
        Component: m.default,
      })),
  },
  {
    path: "*",
    element: <Navigate to="/login" replace />,
  },
]);

export default router;
