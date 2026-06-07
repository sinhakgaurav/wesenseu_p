import type { UserRole } from '@/lib/types'

export const ADMIN_PANEL_ROLES: UserRole[] = [
  'super_admin',
  'property_manager',
  'dept_manager',
  'employee',
  'guest',
]

export function isSuperAdmin(role?: UserRole | string | null): boolean {
  return role === 'super_admin'
}

export function hasRole(role: UserRole | string | undefined | null, allowed: readonly UserRole[]): boolean {
  if (!role) return false
  if (isSuperAdmin(role)) return true
  return (allowed as readonly string[]).includes(role)
}

export type NavEntry = {
  path: string
  roles: readonly UserRole[]
}

/** Property-level operations (all roles). */
export const MAIN_NAV: NavEntry[] = [
  { path: '/admin/dashboard', roles: ['super_admin', 'property_manager', 'dept_manager', 'employee'] },
  { path: '/admin/rooms', roles: ['super_admin', 'property_manager', 'dept_manager'] },
  { path: '/admin/guests', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/benchmarks', roles: ['super_admin', 'property_manager', 'dept_manager'] },
  { path: '/admin/tasks', roles: ['super_admin', 'property_manager', 'dept_manager', 'employee'] },
  { path: '/admin/tickets', roles: ['super_admin', 'property_manager', 'dept_manager', 'employee'] },
  { path: '/admin/employees', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/departments', roles: ['super_admin', 'property_manager', 'dept_manager'] },
  { path: '/admin/inventory', roles: ['super_admin', 'property_manager', 'dept_manager'] },
  { path: '/admin/vendors', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/laundry', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/orders', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/attendance', roles: ['super_admin', 'property_manager', 'dept_manager'] },
  { path: '/admin/feedback', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/surveillance', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/reports', roles: ['super_admin', 'property_manager', 'dept_manager'] },
]

export const SETUP_NAV: NavEntry[] = [
  { path: '/admin/onboarding', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/property-settings', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/fnb', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/task-sla', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/room-categories', roles: ['super_admin', 'property_manager'] },
  { path: '/admin/property-groups', roles: ['super_admin', 'property_manager'] },
]

/** Super admin: platform control (not property-scoped). */
export const PLATFORM_NAV: NavEntry[] = [
  { path: '/admin/platform-dashboard', roles: ['super_admin'] },
  { path: '/admin/super-admin', roles: ['super_admin'] },
  { path: '/admin/properties', roles: ['super_admin'] },
]

/** Super admin: all property-scoped flows under one sidebar group. */
export const BUSINESS_NAV: NavEntry[] = [
  { path: '/admin/dashboard', roles: ['super_admin'] },
  ...MAIN_NAV.filter((n) => n.path !== '/admin/dashboard'),
  ...SETUP_NAV,
]

const ALL_NAV = [...MAIN_NAV, ...SETUP_NAV, ...PLATFORM_NAV, ...BUSINESS_NAV]

export function canAccessPath(role: UserRole | undefined | null, path: string): boolean {
  const entry = ALL_NAV.find((n) => n.path === path)
  if (!entry) return isSuperAdmin(role ?? undefined)
  return hasRole(role ?? undefined, entry.roles)
}

export function filterNavByRole<T extends NavEntry>(entries: T[], role: UserRole | undefined | null): T[] {
  if (!role) return []
  return entries.filter((e) => hasRole(role, e.roles))
}

/** Paths that require a selected property for super_admin. */
export const PROPERTY_SCOPED_PATHS = new Set([
  ...MAIN_NAV.map((n) => n.path),
  ...SETUP_NAV.map((n) => n.path),
])

export function isPropertyScopedPath(path: string): boolean {
  return PROPERTY_SCOPED_PATHS.has(path)
}
