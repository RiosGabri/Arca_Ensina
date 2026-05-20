import { type ReactNode } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { AppShell } from "./components/shell/AppShell";
import Dashboard from "./pages/Dashboard";
import DesignSystem from "./pages/DesignSystem";
import Repositorio from "./pages/Repositorio";
import { PatientCreatePage } from "./features/patient";
import { CalculatorPage, MedicationSelectPage } from "./features/calculator";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { Toaster } from "@/components/ui/sonner";

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

export default function App() {
  return (
    <BrowserRouter>
      <Toaster />
      <Routes>
        <Route element={<ShellLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/_/design-system" element={<DesignSystem />} />
          <Route path="/patients" element={<PatientCreatePage />} />
          <Route path="/medications" element={<MedicationSelectPage />} />
          <Route path="/repositorio" element={<Repositorio />} />
          <Route
            path="/calculator/calculate/:medicationId"
            element={<CalculatorPage />}
          />
        </Route>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
