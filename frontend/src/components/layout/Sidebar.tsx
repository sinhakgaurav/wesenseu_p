import { NavLink } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  LayoutDashboard, Users, BedDouble, ClipboardList, Ticket,
  Package, BarChart2, Camera, LogOut, ChevronRight, Star,
  Building2, Shield, ShoppingCart, CalendarClock, Image, Settings, Shirt, UserRound,
  Tags, FolderTree, Rocket, Settings2, UtensilsCrossed, Timer, Truck, Database, Layers,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import clsx from 'clsx'
import { logout } from '@/store/authSlice'
import type { AppDispatch, RootState } from '@/store'
import {
  MAIN_NAV,
  SETUP_NAV,
  PLATFORM_NAV,
  BUSINESS_NAV,
  filterNavByRole,
  isSuperAdmin,
} from '@/lib/rbac'
import type { UserRole } from '@/lib/types'
import { usePropertyScope } from '@/context/PropertyScopeContext'

type NavMeta = { label: string; icon: LucideIcon }

const NAV_META: Record<string, NavMeta> = {
  '/admin/platform-dashboard': { label: 'Platform Dashboard', icon: Layers },
  '/admin/dashboard': { label: 'Property Dashboard', icon: LayoutDashboard },
  '/admin/rooms': { label: 'Rooms', icon: BedDouble },
  '/admin/guests': { label: 'Guests', icon: UserRound },
  '/admin/benchmarks': { label: 'Benchmarks', icon: Image },
  '/admin/tasks': { label: 'Tasks', icon: ClipboardList },
  '/admin/tickets': { label: 'Tickets', icon: Ticket },
  '/admin/employees': { label: 'Employees', icon: Users },
  '/admin/departments': { label: 'Departments', icon: Building2 },
  '/admin/inventory': { label: 'Inventory', icon: Package },
  '/admin/vendors': { label: 'Vendors', icon: Truck },
  '/admin/laundry': { label: 'Laundry', icon: Shirt },
  '/admin/orders': { label: 'Orders', icon: ShoppingCart },
  '/admin/attendance': { label: 'Attendance', icon: CalendarClock },
  '/admin/feedback': { label: 'Feedback', icon: Star },
  '/admin/surveillance': { label: 'Surveillance', icon: Camera },
  '/admin/reports': { label: 'Reports', icon: BarChart2 },
  '/admin/onboarding': { label: 'Onboarding', icon: Rocket },
  '/admin/property-settings': { label: 'Property Settings', icon: Settings2 },
  '/admin/fnb': { label: 'F&B', icon: UtensilsCrossed },
  '/admin/task-sla': { label: 'Task SLA', icon: Timer },
  '/admin/room-categories': { label: 'Room Categories', icon: Tags },
  '/admin/property-groups': { label: 'Property Groups', icon: FolderTree },
  '/admin/properties': { label: 'Properties', icon: Building2 },
  '/admin/super-admin': { label: 'Admin Panel', icon: Settings },
}

function resolveNav(entries: { path: string; roles: readonly UserRole[] }[], role: UserRole | undefined) {
  return filterNavByRole(entries, role)
    .map((e) => {
      const meta = NAV_META[e.path]
      if (!meta) return null
      return { path: e.path, label: meta.label, icon: meta.icon }
    })
    .filter((x): x is { path: string; label: string; icon: LucideIcon } => x != null)
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  clsx(
    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
    isActive
      ? 'bg-blue-600 text-white shadow-sm shadow-blue-900/30'
      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
  )

function NavSection({
  items,
  collapsed,
  title,
}: {
  items: { path: string; label: string; icon: LucideIcon }[]
  collapsed: boolean
  title?: string
}) {
  if (items.length === 0) return null
  return (
    <>
      {title && !collapsed && (
        <p className="px-3 pt-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {title}
        </p>
      )}
      {items.map(({ path, label, icon: Icon }) => (
        <NavLink key={path} to={path} className={navLinkClass}>
          {({ isActive }) => (
            <>
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
              {!collapsed && isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
            </>
          )}
        </NavLink>
      ))}
    </>
  )
}

export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  const dispatch = useDispatch<AppDispatch>()
  const user = useSelector((state: RootState) => state.auth.user)
  const role = user?.role
  const superAdmin = isSuperAdmin(role)
  const { properties, selectedPropertyId, setSelectedPropertyId } = usePropertyScope()

  const platformItems = resolveNav(PLATFORM_NAV, role)
  const businessItems = resolveNav(BUSINESS_NAV, role)
  const mainItems = superAdmin ? [] : resolveNav(MAIN_NAV, role)
  const setupItems = superAdmin ? [] : resolveNav(SETUP_NAV, role)

  return (
    <aside className={clsx(
      'bg-gray-900 text-white flex flex-col h-full transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    )}>
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-lg font-bold text-white">Monitour</h1>
              <p className="text-xs text-gray-400">{superAdmin ? 'Platform' : 'Operations'}</p>
            </div>
          )}
        </div>
      </div>

      {!collapsed && user && (
        <div className="px-4 py-3 border-b border-gray-800 space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
              {user.full_name[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role.replace(/_/g, ' ')}</p>
            </div>
          </div>
          {superAdmin && properties.length > 0 && (
            <select
              className="w-full text-xs bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-gray-200"
              value={selectedPropertyId || ''}
              onChange={(e) => setSelectedPropertyId(e.target.value || null)}
            >
              <option value="">Business property…</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
        </div>
      )}

      <nav className="flex-1 py-4 overflow-y-auto scrollbar-hide">
        <div className="px-2 space-y-1">
          {superAdmin && <NavSection items={platformItems} collapsed={collapsed} title="Platform" />}
          {superAdmin && <NavSection items={businessItems} collapsed={collapsed} title="Business Management" />}
          {!superAdmin && <NavSection items={mainItems} collapsed={collapsed} title="Operations" />}
          {!superAdmin && <NavSection items={setupItems} collapsed={collapsed} title="Setup" />}
        </div>
      </nav>

      {!collapsed && (
        <div className="px-4 py-2 border-t border-gray-800 flex gap-3">
          <NavLink to="/" className={({ isActive }) => clsx('text-xs hover:text-gray-300', isActive ? 'text-blue-400 font-medium' : 'text-gray-500')}>Home</NavLink>
          <NavLink to="/pricing" className={({ isActive }) => clsx('text-xs hover:text-gray-300', isActive ? 'text-blue-400 font-medium' : 'text-gray-500')}>Pricing</NavLink>
        </div>
      )}

      <div className="p-2 border-t border-gray-800">
        <button
          onClick={() => dispatch(logout())}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
