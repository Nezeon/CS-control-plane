import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, LazyMotion, domAnimation } from 'framer-motion'
import useAuthStore from './stores/authStore'
import ProtectedRoute from './components/layout/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import PageTransition from './components/layout/PageTransition'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CustomersPage from './pages/CustomersPage'
import CustomerDetailPage from './pages/CustomerDetailPage'
import AgentsPage from './pages/AgentsPage'
import TicketsPage from './pages/TicketsPage'
import AlertsPage from './pages/AlertsPage'
import AskPage from './pages/AskPage'
import ExecutivePage from './pages/ExecutivePage'

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageTransition><DashboardPage /></PageTransition>} />
        <Route path="/customers" element={<PageTransition><CustomersPage /></PageTransition>} />
        <Route path="/customers/:id" element={<PageTransition><CustomerDetailPage /></PageTransition>} />
        <Route path="/tickets" element={<PageTransition><TicketsPage /></PageTransition>} />
        <Route path="/agents" element={<PageTransition><AgentsPage /></PageTransition>} />
        <Route path="/alerts" element={<PageTransition><AlertsPage /></PageTransition>} />
        <Route path="/ask" element={<PageTransition><AskPage /></PageTransition>} />
        <Route path="/executive" element={<PageTransition><ExecutivePage /></PageTransition>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <LazyMotion features={domAnimation} strict>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <AnimatedRoutes />
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </LazyMotion>
  )
}
