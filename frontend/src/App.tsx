import { type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import DesignSystem from "./pages/DesignSystem";
import { PatientCreatePage } from "./features/patient";
import { CalculatorPage, MedicationSelectPage } from "./features/calculator";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { Toaster } from "@/components/ui/sonner";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <p className="text-center mt-20">Carregando...</p>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster />
      <Routes>
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/_/design-system"
          element={
            <ProtectedRoute>
              <DesignSystem />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patients"
          element={
            <ProtectedRoute>
              <PatientCreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/calculator/calculate/:medicationId"
          element={
            <ProtectedRoute>
              <CalculatorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/medications"
          element={
            <ProtectedRoute>
              <MedicationSelectPage />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
