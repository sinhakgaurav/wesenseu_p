import { useQuery } from '@tanstack/react-query'
import { Building2, Users, BedDouble, ClipboardList, Ticket } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { StatCard } from '@/components/ui/StatCard'
import { usePropertyScope } from '@/context/PropertyScopeContext'

type PlatformStats = {
  total_properties: number
  active_properties: number
  total_customers: number
  total_rooms: number
  open_tasks: number
  open_tickets: number
  total_employees: number
  properties: {
    property_id: string
    property_name: string
    city?: string
    total_rooms: number
    open_tasks: number
    open_tickets: number
    occupancy_pct: number
  }[]
}

export function PlatformDashboardPage() {
  const { setSelectedPropertyId } = usePropertyScope()

  const { data, isLoading } = useQuery<PlatformStats>({
    queryKey: ['platform-dashboard'],
    queryFn: () => api.get('/dashboard/platform').then((r) => r.data),
    refetchInterval: 60000,
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Dashboard</h1>
          <p className="text-gray-500 text-sm">All hotels — multi-property operations overview</p>
        </div>
        <Link to="/admin/super-admin" className="btn-secondary text-sm">Admin Panel</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard title="Properties" value={data?.total_properties ?? 0} icon={Building2} iconBg="bg-blue-50" iconColor="text-blue-600" />
        <StatCard title="Active" value={data?.active_properties ?? 0} icon={Building2} iconBg="bg-green-50" iconColor="text-green-600" />
        <StatCard title="Businesses" value={data?.total_customers ?? 0} icon={Users} iconBg="bg-purple-50" iconColor="text-purple-600" />
        <StatCard title="Total rooms" value={data?.total_rooms ?? 0} icon={BedDouble} iconBg="bg-teal-50" iconColor="text-teal-600" />
        <StatCard title="Open tasks" value={data?.open_tasks ?? 0} icon={ClipboardList} iconBg="bg-orange-50" iconColor="text-orange-600" />
        <StatCard title="Open tickets" value={data?.open_tickets ?? 0} icon={Ticket} iconBg="bg-red-50" iconColor="text-red-600" />
        <StatCard title="Employees" value={data?.total_employees ?? 0} icon={Users} iconBg="bg-indigo-50" iconColor="text-indigo-600" />
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Properties at a glance</h3>
        {!data?.properties?.length ? (
          <p className="text-sm text-gray-500">No properties. Run seed or create via Properties.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b">
                  <th className="py-2">Property</th>
                  <th className="py-2">Rooms</th>
                  <th className="py-2">Occupancy</th>
                  <th className="py-2">Tasks</th>
                  <th className="py-2">Tickets</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {data.properties.map((p) => (
                  <tr key={p.property_id} className="border-b border-gray-50">
                    <td className="py-3 font-medium">{p.property_name}{p.city && <span className="text-gray-400 font-normal"> · {p.city}</span>}</td>
                    <td>{p.total_rooms}</td>
                    <td>{p.occupancy_pct}%</td>
                    <td>{p.open_tasks}</td>
                    <td>{p.open_tickets}</td>
                    <td>
                      <button
                        type="button"
                        className="text-blue-600 text-xs hover:underline"
                        onClick={() => {
                          setSelectedPropertyId(p.property_id)
                          window.location.href = '/admin/dashboard'
                        }}
                      >
                        Open ops →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
