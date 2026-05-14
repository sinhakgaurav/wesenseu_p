import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider, useSelector } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { store } from './store'
import type { RootState } from './store'

import { LoginPage } from './pages/LoginPage'
import { AdminLayout } from './components/layout/AdminLayout'
import { DashboardPage } from './pages/admin/DashboardPage'
import { RoomsPage } from './pages/admin/RoomsPage'
import { TasksPage } from './pages/admin/TasksPage'
import { TicketsPage } from './pages/admin/TicketsPage'
import { EmployeesPage } from './pages/admin/EmployeesPage'
import { DepartmentsPage } from './pages/admin/DepartmentsPage'
import { InventoryPage } from './pages/admin/InventoryPage'
import { FeedbackPage } from './pages/admin/FeedbackPage'
import { SurveillancePage } from './pages/admin/SurveillancePage'
import { ReportsPage } from './pages/admin/ReportsPage'
import { OrdersPage } from './pages/admin/OrdersPage'
import { AttendancePage } from './pages/admin/AttendancePage'
import { BenchmarksPage } from './pages/admin/BenchmarksPage'
import { RoomCategoriesPage } from './pages/admin/RoomCategoriesPage'
import { PropertyGroupsPage } from './pages/admin/PropertyGroupsPage'
import { LaundryPage } from './pages/admin/LaundryPage'
import { GuestStaysPage } from './pages/admin/GuestStaysPage'
import { GuestPortalPage } from './pages/guest/GuestPortalPage'
import { LandingPage } from './pages/public/LandingPage'
import { AboutPage } from './pages/public/AboutPage'
import { PricingPage } from './pages/public/PricingPage'
import { ContactPage } from './pages/public/ContactPage'
import { SupportChatPage } from './pages/public/SupportChatPage'
import { AdminPanelPage } from './pages/super_admin/AdminPanelPage'
import { SupportChatWidget } from './components/SupportChatWidget'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function SuperAdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role !== 'super_admin') return <Navigate to="/admin/dashboard" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public marketing pages */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/support" element={<SupportChatPage />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/guest/:roomId" element={<GuestPortalPage />} />

      {/* Admin panel for property ops */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="rooms" element={<RoomsPage />} />
        <Route path="guests" element={<GuestStaysPage />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="employees" element={<EmployeesPage />} />
        <Route path="departments" element={<DepartmentsPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="laundry" element={<LaundryPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="attendance" element={<AttendancePage />} />
        <Route path="feedback" element={<FeedbackPage />} />
        <Route path="surveillance" element={<SurveillancePage />} />
        <Route path="benchmarks" element={<BenchmarksPage />} />
        <Route path="room-categories" element={<RoomCategoriesPage />} />
        <Route path="property-groups" element={<PropertyGroupsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        {/* Super-admin panel nested under /admin for authenticated layout */}
        <Route
          path="super-admin"
          element={
            <SuperAdminRoute>
              <AdminPanelPage />
            </SuperAdminRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppRoutes />
          <SupportChatWidget />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                borderRadius: '12px',
                background: '#1f2937',
                color: '#fff',
                fontSize: '14px',
              },
              success: { iconTheme: { primary: '#22c55e', secondary: '#fff' } },
              error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
            }}
          />
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  )
}
