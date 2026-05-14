import { NavLink } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  LayoutDashboard, Users, BedDouble, ClipboardList, Ticket,
  Package, BarChart2, Camera, LogOut, ChevronRight, Star,
  Building2, Shield, ShoppingCart, CalendarClock, Image, Settings, Shirt, UserRound,
  Tags, FolderTree,
} from 'lucide-react'
import clsx from 'clsx'
import { logout } from '@/store/authSlice'
import type { AppDispatch, RootState } from '@/store'

const navItems = [
  { path: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/admin/rooms', label: 'Rooms', icon: BedDouble },
  { path: '/admin/guests', label: 'Guests', icon: UserRound },
  { path: '/admin/benchmarks', label: 'Benchmarks', icon: Image },
  { path: '/admin/tasks', label: 'Tasks', icon: ClipboardList },
  { path: '/admin/tickets', label: 'Tickets', icon: Ticket },
  { path: '/admin/employees', label: 'Employees', icon: Users },
  { path: '/admin/departments', label: 'Departments', icon: Building2 },
  { path: '/admin/inventory', label: 'Inventory', icon: Package },
  { path: '/admin/laundry', label: 'Laundry', icon: Shirt },
  { path: '/admin/orders', label: 'Orders', icon: ShoppingCart },
  { path: '/admin/attendance', label: 'Attendance', icon: CalendarClock },
  { path: '/admin/feedback', label: 'Feedback', icon: Star },
  { path: '/admin/surveillance', label: 'Surveillance', icon: Camera },
  { path: '/admin/reports', label: 'Reports', icon: BarChart2 },
]

const setupNavItems = [
  { path: '/admin/room-categories', label: 'Room Categories', icon: Tags },
  { path: '/admin/property-groups', label: 'Property Groups', icon: FolderTree },
]

const adminOnlyItems = [
  { path: '/admin/super-admin', label: 'Admin Panel', icon: Settings },
]

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  clsx(
    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
    isActive
      ? 'bg-blue-600 text-white shadow-sm shadow-blue-900/30'
      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
  )

export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  const dispatch = useDispatch<AppDispatch>()
  const user = useSelector((state: RootState) => state.auth.user)

  return (
    <aside className={clsx(
      'bg-gray-900 text-white flex flex-col h-full transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-lg font-bold text-white">Monitour</h1>
              <p className="text-xs text-gray-400">Operations Platform</p>
            </div>
          )}
        </div>
      </div>

      {/* User info */}
      {!collapsed && user && (
        <div className="px-4 py-3 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
              {user.full_name[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role.replace(/_/g, ' ')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto scrollbar-hide">
        <div className="px-2 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
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

          {(user?.role === 'super_admin' || user?.role === 'property_manager') && (
            <>
              {!collapsed && (
                <p className="px-3 pt-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Setup
                </p>
              )}
              {setupNavItems.map(({ path, label, icon: Icon }) => (
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
          )}

          {user?.role === 'super_admin' && (
            <>
              {!collapsed && (
                <p className="px-3 pt-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Super Admin
                </p>
              )}
              {adminOnlyItems.map(({ path, label, icon: Icon }) => (
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
          )}
        </div>
      </nav>

      {/* Footer links */}
      {!collapsed && (
        <div className="px-4 py-2 border-t border-gray-800 flex gap-3">
          <NavLink to="/"        className={({ isActive }) => clsx('text-xs hover:text-gray-300', isActive ? 'text-blue-400 font-medium' : 'text-gray-500')}>Home</NavLink>
          <NavLink to="/pricing" className={({ isActive }) => clsx('text-xs hover:text-gray-300', isActive ? 'text-blue-400 font-medium' : 'text-gray-500')}>Pricing</NavLink>
        </div>
      )}

      {/* Logout */}
      <div className="p-2 border-t border-gray-800">
        <button
          onClick={() => dispatch(logout())}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:bg-gray-800 hover:text-white transition-all"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
