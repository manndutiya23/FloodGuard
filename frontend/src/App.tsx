import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ReportPage from './pages/ReportPage'
import ResponderDashboard from './pages/ResponderDashboard'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="report" element={<ReportPage />} />
        <Route path="responder" element={<ResponderDashboard />} />
        <Route
          path="*"
          element={<main className="mx-auto max-w-[1360px] p-6">Page not found.</main>}
        />
      </Route>
    </Routes>
  )
}
