import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import CustomerDetailPage from './pages/CustomerDetailPage'
import PipelineAnalyticsPage from './pages/PipelineAnalyticsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/customers/:id" element={<CustomerDetailPage />} />
          <Route path="/pipeline" element={<PipelineAnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}
