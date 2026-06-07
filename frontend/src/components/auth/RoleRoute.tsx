import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import type { UserRole } from '@/lib/types'
import { hasRole } from '@/lib/rbac'

type RoleRouteProps = {
  children: React.ReactNode
  /** Allowed roles. `super_admin` always passes via hasRole(). */
  roles: readonly UserRole[]
  fallback?: string
}

export function RoleRoute({ children, roles, fallback = '/admin/dashboard' }: RoleRouteProps) {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!hasRole(user?.role, roles)) return <Navigate to={fallback} replace />
  return <>{children}</>
}

/** Strict super_admin only (no shared manager routes). */
export function SuperAdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role !== 'super_admin') return <Navigate to="/admin/dashboard" replace />
  return <>{children}</>
}
