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
import { OnboardingWizardPage } from './pages/admin/OnboardingWizardPage'
import { PropertySettingsPage } from './pages/admin/PropertySettingsPage'
import { FnBPage } from './pages/admin/FnBPage'
import { TaskSlaPage } from './pages/admin/TaskSlaPage'
import { PropertiesPage } from './pages/admin/PropertiesPage'
import { VendorsPage } from './pages/admin/VendorsPage'
import { GuestPortalPage } from './pages/guest/GuestPortalPage'
import { LandingPage } from './pages/public/LandingPage'
import { AboutPage } from './pages/public/AboutPage'
import { PricingPage } from './pages/public/PricingPage'
import { ContactPage } from './pages/public/ContactPage'
import { SupportChatPage } from './pages/public/SupportChatPage'
import { AdminPanelPage } from './pages/super_admin/AdminPanelPage'
import { PlatformDashboardPage } from './pages/admin/PlatformDashboardPage'
import { SupportChatWidget } from './components/SupportChatWidget'
import { RoleRoute, SuperAdminRoute } from './components/auth/RoleRoute'
import { canAccessPath } from './lib/rbac'
import type { UserRole } from './lib/types'

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

function AdminPageRoute({
  path,
  children,
}: {
  path: string
  children: React.ReactNode
}) {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!canAccessPath(user?.role, path)) return <Navigate to="/admin/dashboard" replace />
  return <>{children}</>
}

const SETUP_ROLES = ['super_admin', 'property_manager'] as const satisfies readonly UserRole[]

function AdminIndexRedirect() {
  const user = useSelector((state: RootState) => state.auth.user)
  if (user?.role === 'super_admin') return <Navigate to="/admin/platform-dashboard" replace />
  return <Navigate to="/admin/dashboard" replace />
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
        <Route index element={<AdminIndexRedirect />} />
        <Route path="platform-dashboard" element={<SuperAdminRoute><PlatformDashboardPage /></SuperAdminRoute>} />
        <Route path="dashboard" element={<AdminPageRoute path="/admin/dashboard"><DashboardPage /></AdminPageRoute>} />
        <Route path="rooms" element={<AdminPageRoute path="/admin/rooms"><RoomsPage /></AdminPageRoute>} />
        <Route path="guests" element={<AdminPageRoute path="/admin/guests"><GuestStaysPage /></AdminPageRoute>} />
        <Route path="tasks" element={<AdminPageRoute path="/admin/tasks"><TasksPage /></AdminPageRoute>} />
        <Route path="tickets" element={<AdminPageRoute path="/admin/tickets"><TicketsPage /></AdminPageRoute>} />
        <Route path="employees" element={<AdminPageRoute path="/admin/employees"><EmployeesPage /></AdminPageRoute>} />
        <Route path="departments" element={<AdminPageRoute path="/admin/departments"><DepartmentsPage /></AdminPageRoute>} />
        <Route path="inventory" element={<AdminPageRoute path="/admin/inventory"><InventoryPage /></AdminPageRoute>} />
        <Route path="vendors" element={<AdminPageRoute path="/admin/vendors"><VendorsPage /></AdminPageRoute>} />
        <Route path="laundry" element={<AdminPageRoute path="/admin/laundry"><LaundryPage /></AdminPageRoute>} />
        <Route path="orders" element={<AdminPageRoute path="/admin/orders"><OrdersPage /></AdminPageRoute>} />
        <Route path="attendance" element={<AdminPageRoute path="/admin/attendance"><AttendancePage /></AdminPageRoute>} />
        <Route path="feedback" element={<AdminPageRoute path="/admin/feedback"><FeedbackPage /></AdminPageRoute>} />
        <Route path="surveillance" element={<AdminPageRoute path="/admin/surveillance"><SurveillancePage /></AdminPageRoute>} />
        <Route path="benchmarks" element={<AdminPageRoute path="/admin/benchmarks"><BenchmarksPage /></AdminPageRoute>} />
        <Route path="reports" element={<AdminPageRoute path="/admin/reports"><ReportsPage /></AdminPageRoute>} />
        <Route path="room-categories" element={<RoleRoute roles={SETUP_ROLES}><RoomCategoriesPage /></RoleRoute>} />
        <Route path="onboarding" element={<RoleRoute roles={SETUP_ROLES}><OnboardingWizardPage /></RoleRoute>} />
        <Route path="property-settings" element={<RoleRoute roles={SETUP_ROLES}><PropertySettingsPage /></RoleRoute>} />
        <Route path="fnb" element={<RoleRoute roles={SETUP_ROLES}><FnBPage /></RoleRoute>} />
        <Route path="task-sla" element={<RoleRoute roles={SETUP_ROLES}><TaskSlaPage /></RoleRoute>} />
        <Route path="property-groups" element={<RoleRoute roles={SETUP_ROLES}><PropertyGroupsPage /></RoleRoute>} />
        <Route path="properties" element={<SuperAdminRoute><PropertiesPage /></SuperAdminRoute>} />
        <Route path="super-admin" element={<SuperAdminRoute><AdminPanelPage /></SuperAdminRoute>} />
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
